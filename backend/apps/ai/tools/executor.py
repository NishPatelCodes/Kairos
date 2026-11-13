import json
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from apps.accounts.models import UserPreference, UserProfile
from apps.common.timeutils import user_today
from apps.goals.models import AnnualGoal, MonthlyGoal
from apps.progress.services import daily_progress, monthly_progress
from apps.schedule.engine import engine, parse_date, parse_time
from apps.schedule.models import ScheduleItem
from apps.schedule.serializers import ScheduleItemSerializer

from ..recommendation import recommend_next


ALLOWED_TOOLS = {
    "get_today_schedule",
    "get_monthly_goals",
    "get_annual_goal",
    "get_recent_activity",
    "get_free_slots",
    "create_schedule_item",
    "apply_day_plan",
    "update_schedule_item",
    "delete_schedule_item",
    "move_schedule_item",
    "complete_task",
    "increment_goal_progress",
    "create_goal",
    "update_goal",
    "update_preferences",
    "get_productivity_insights",
}


def _ok(payload, ui=None):
    return {"ok": True, "data": payload, "ui": ui}


def _err(message, extra=None):
    body = {"ok": False, "error": message}
    if extra:
        body.update(extra)
    return body


def _item_ui(item: ScheduleItem) -> dict:
    return {
        "type": "schedule_item",
        "item": ScheduleItemSerializer(item).data,
    }


def _own_item(user, item_id):
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        raise ValidationError("Invalid schedule item id.")
    item = ScheduleItem.objects.filter(user=user, pk=item_id).first()
    if not item:
        raise ValidationError("Schedule item not found.")
    return item


def _own_monthly(user, goal_id):
    try:
        goal_id = int(goal_id)
    except (TypeError, ValueError):
        raise ValidationError("Invalid goal id.")
    goal = MonthlyGoal.objects.filter(user=user, pk=goal_id).first()
    if not goal:
        raise ValidationError("Monthly goal not found.")
    return goal


class ToolExecutor:
    def execute(self, user, name: str, arguments: dict) -> dict:
        if name not in ALLOWED_TOOLS:
            return _err(f"Unknown tool '{name}'.")
        arguments = arguments or {}
        try:
            handler = getattr(self, name)
            return handler(user, arguments)
        except ValidationError as exc:
            detail = exc.detail if hasattr(exc, "detail") else str(exc)
            return _err("Validation failed.", {"detail": detail})
        except DjangoValidationError as exc:
            return _err("Validation failed.", {"detail": exc.message_dict if hasattr(exc, "message_dict") else str(exc)})
        except Exception as exc:  # noqa: BLE001 — surface tool errors to the model, never crash the loop
            return _err(str(exc))

    def get_today_schedule(self, user, args):
        day = parse_date(args.get("date"), user)
        items = engine.for_day(user, day)
        return _ok(
            {
                "date": str(day),
                "items": ScheduleItemSerializer(items, many=True).data,
            }
        )

    def get_monthly_goals(self, user, args):
        month = parse_date(args.get("month"), user).replace(day=1)
        goals = MonthlyGoal.objects.filter(user=user, month=month)
        return _ok(
            [
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "metric_current": g.metric_current,
                    "metric_target": g.metric_target,
                    "metric_unit": g.metric_unit,
                    "priority": g.priority,
                    "status": g.status,
                    "progress_pct": g.progress_pct,
                }
                for g in goals
            ]
        )

    def get_annual_goal(self, user, _args):
        goal = AnnualGoal.objects.filter(user=user, is_active=True).first()
        if not goal:
            return _ok(None)
        today = user_today(user)
        return _ok(
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "target_date": str(goal.target_date),
                "days_remaining": (goal.target_date - today).days,
            }
        )

    def get_recent_activity(self, user, _args):
        today = user_today(user)
        recent = ScheduleItem.objects.filter(user=user, date__gte=today - timedelta(days=7)).order_by("-date")
        return _ok(
            {
                "daily_progress": daily_progress(user, today),
                "recent": [
                    {
                        "id": i.id,
                        "date": str(i.date),
                        "title": i.title,
                        "status": i.status,
                        "start_time": i.start_time.strftime("%H:%M"),
                    }
                    for i in recent[:40]
                ],
            }
        )

    def get_free_slots(self, user, args):
        day = parse_date(args.get("date"), user)
        prefs = getattr(user, "preferences", None)
        start = prefs.work_start if prefs and prefs.work_start else parse_time("08:00")
        end = prefs.work_end if prefs and prefs.work_end else parse_time("22:00")
        min_minutes = int(args.get("min_minutes") or 25)
        return _ok(engine.free_slots(user, day, start, end, min_minutes=min_minutes))

    def create_schedule_item(self, user, args):
        goal_id = args.get("goal_id")
        if goal_id:
            _own_monthly(user, goal_id)
        item = engine.create(
            user,
            title=args.get("title"),
            day=parse_date(args.get("date"), user),
            start=parse_time(str(args.get("start_time"))),
            end=parse_time(str(args.get("end_time"))),
            monthly_goal_id=goal_id,
            notes=args.get("notes") or "",
            kind=args.get("kind") or "focus",
            is_fixed=bool(args.get("is_fixed")),
            created_by="ai",
        )
        return _ok(ScheduleItemSerializer(item).data, ui=_item_ui(item))

    def apply_day_plan(self, user, args):
        blocks = args.get("items") or []
        if not isinstance(blocks, list) or not blocks:
            return _err("items must be a non-empty list of schedule blocks.")
        for block in blocks:
            if block.get("goal_id"):
                _own_monthly(user, block["goal_id"])
        created = engine.apply_day_plan(
            user,
            parse_date(args.get("date"), user),
            blocks,
            keep_completed=True,
        )
        data = ScheduleItemSerializer(created, many=True).data
        return _ok(
            {"replaced": True, "items": data},
            ui={"type": "schedule_plan", "items": data},
        )

    def update_schedule_item(self, user, args):
        item = _own_item(user, args.get("id"))
        fields = {}
        if args.get("title"):
            fields["title"] = args["title"]
        if args.get("notes") is not None:
            fields["notes"] = args["notes"]
        if args.get("date"):
            fields["date"] = parse_date(args["date"], user)
        if args.get("start_time"):
            fields["start_time"] = parse_time(str(args["start_time"]))
        if args.get("end_time"):
            fields["end_time"] = parse_time(str(args["end_time"]))
        if args.get("status"):
            fields["status"] = args["status"]
        if "goal_id" in args:
            if args["goal_id"]:
                _own_monthly(user, args["goal_id"])
            fields["monthly_goal_id"] = args["goal_id"] or None
        updated = engine.update(user, item.id, **fields)
        return _ok(ScheduleItemSerializer(updated).data, ui=_item_ui(updated))

    def delete_schedule_item(self, user, args):
        item = _own_item(user, args.get("id"))
        engine.delete(user, item.id)
        return _ok({"deleted": item.id})

    def move_schedule_item(self, user, args):
        item = _own_item(user, args.get("id"))
        moved = engine.move(
            user,
            item.id,
            start=parse_time(str(args.get("start_time"))),
            end=parse_time(str(args.get("end_time"))),
            day=parse_date(args.get("date"), user) if args.get("date") else item.date,
        )
        return _ok(ScheduleItemSerializer(moved).data, ui=_item_ui(moved))

    def complete_task(self, user, args):
        item = _own_item(user, args.get("id"))
        amount = args.get("progress_amount")
        if amount is not None:
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                return _err("progress_amount must be a number.")
        goal_id = args.get("goal_id")
        if goal_id not in (None, ""):
            try:
                goal_id = int(goal_id)
            except (TypeError, ValueError):
                return _err("goal_id must be an integer.")
        else:
            goal_id = None
        done = engine.complete(user, item.id, progress_amount=amount, goal_id=goal_id)
        payload = ScheduleItemSerializer(done).data
        if done.monthly_goal_id:
            payload["goal_progress"] = {
                "id": done.monthly_goal_id,
                "title": done.monthly_goal.title if done.monthly_goal else None,
                "metric_current": done.monthly_goal.metric_current if done.monthly_goal else None,
                "metric_target": done.monthly_goal.metric_target if done.monthly_goal else None,
                "progress_pct": done.monthly_goal.progress_pct if done.monthly_goal else None,
            }
        return _ok(payload, ui=_item_ui(done))

    def increment_goal_progress(self, user, args):
        goal = _own_monthly(user, args.get("goal_id"))
        try:
            amount = float(args.get("amount"))
        except (TypeError, ValueError):
            return _err("amount must be a number.")
        updated = engine.increment_goal(user, goal.id, amount)
        return _ok(
            {
                "id": updated.id,
                "title": updated.title,
                "metric_current": updated.metric_current,
                "metric_target": updated.metric_target,
                "metric_unit": updated.metric_unit,
                "progress_pct": updated.progress_pct,
            }
        )

    def create_goal(self, user, args):
        level = args.get("level")
        title = (args.get("title") or "").strip()
        if not title:
            return _err("Title is required.")
        if level == "annual":
            target = parse_date(args.get("target_date"), user)
            AnnualGoal.objects.filter(user=user, is_active=True).update(is_active=False)
            goal = AnnualGoal.objects.create(
                user=user,
                title=title,
                description=args.get("description") or "",
                target_date=target,
                is_active=True,
            )
            return _ok(
                {
                    "id": goal.id,
                    "level": "annual",
                    "title": goal.title,
                    "target_date": str(goal.target_date),
                }
            )
        if level == "monthly":
            month = parse_date(args.get("month"), user).replace(day=1)
            annual = AnnualGoal.objects.filter(user=user, is_active=True).first()
            goal = MonthlyGoal.objects.create(
                user=user,
                annual_goal=annual,
                title=title,
                description=args.get("description") or "",
                metric_target=args.get("metric_target"),
                metric_unit=args.get("metric_unit") or "",
                month=month,
                priority=int(args.get("priority") or 3),
            )
            return _ok(
                {
                    "id": goal.id,
                    "level": "monthly",
                    "title": goal.title,
                    "metric_target": goal.metric_target,
                    "metric_unit": goal.metric_unit,
                    "priority": goal.priority,
                }
            )
        return _err("level must be 'annual' or 'monthly'.")

    def update_goal(self, user, args):
        level = args.get("level")
        try:
            goal_id = int(args.get("id"))
        except (TypeError, ValueError):
            return _err("Invalid goal id.")
        if level == "annual":
            goal = AnnualGoal.objects.filter(user=user, pk=goal_id).first()
            if not goal:
                return _err("Annual goal not found.")
            if args.get("title"):
                goal.title = args["title"]
            if args.get("description") is not None:
                goal.description = args["description"]
            goal.save()
            return _ok({"id": goal.id, "level": "annual", "title": goal.title})
        if level == "monthly":
            goal = _own_monthly(user, goal_id)
            for field in ("title", "description", "metric_unit", "status"):
                if args.get(field) is not None:
                    setattr(goal, field, args[field])
            if args.get("metric_target") is not None:
                goal.metric_target = args["metric_target"]
            if args.get("metric_current") is not None:
                goal.metric_current = args["metric_current"]
            if args.get("priority") is not None:
                goal.priority = int(args["priority"])
            goal.save()
            return _ok(
                {
                    "id": goal.id,
                    "level": "monthly",
                    "title": goal.title,
                    "metric_current": goal.metric_current,
                    "metric_target": goal.metric_target,
                    "progress_pct": goal.progress_pct,
                }
            )
        return _err("level must be 'annual' or 'monthly'.")

    def update_preferences(self, user, args):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        prefs, _ = UserPreference.objects.get_or_create(user=user)
        if args.get("peak_energy") in {"morning", "afternoon", "evening"}:
            profile.peak_energy = args["peak_energy"]
        if args.get("typical_weekday") is not None:
            profile.typical_weekday = args["typical_weekday"]
        if args.get("blockers") is not None:
            profile.blockers = args["blockers"]
        if args.get("onboarding_completed") is not None:
            profile.onboarding_completed = bool(args["onboarding_completed"])
        profile.save()
        if args.get("work_start"):
            prefs.work_start = parse_time(str(args["work_start"]))
        if args.get("work_end"):
            prefs.work_end = parse_time(str(args["work_end"]))
        if args.get("preferred_block_minutes"):
            prefs.preferred_block_minutes = int(args["preferred_block_minutes"])
        prefs.save()
        return _ok({"updated": True, "onboarding_completed": profile.onboarding_completed})

    def get_productivity_insights(self, user, _args):
        return _ok(
            {
                "daily": daily_progress(user),
                "monthly": monthly_progress(user),
                "recommendation": recommend_next(user),
            }
        )


executor = ToolExecutor()
