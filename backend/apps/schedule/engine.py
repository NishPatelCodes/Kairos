from datetime import date, datetime, time
from typing import Optional

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.timeutils import combine_local, user_now, user_today

from .models import ScheduleItem


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def parse_time(value: str) -> time:
    value = (value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(value, fmt).time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    raise ValidationError({"start_time": f"Could not parse time '{value}'. Use HH:MM."})


def parse_date(value: str | date | None, user) -> date:
    if value is None or value == "":
        return user_today(user)
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError({"date": f"Could not parse date '{value}'."}) from exc


class ScheduleEngine:
    """Deterministic scheduling. The LLM never writes directly to the database."""

    def overlapping(self, user, day: date, start: time, end: time, exclude_id: Optional[int] = None):
        qs = ScheduleItem.objects.filter(user=user, date=day).exclude(
            status__in=["rescheduled", "completed"]
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        conflicts = []
        start_m, end_m = _to_minutes(start), _to_minutes(end)
        if end_m <= start_m:
            raise ValidationError({"end_time": "End time must be after start time."})
        for item in qs:
            other_s, other_e = _to_minutes(item.start_time), _to_minutes(item.end_time)
            if start_m < other_e and end_m > other_s:
                conflicts.append(item)
        return conflicts

    def refresh_statuses(self, user, day: date | None = None) -> None:
        day = day or user_today(user)
        now = user_now(user)
        items = ScheduleItem.objects.filter(user=user, date=day).exclude(status="rescheduled")
        for item in items:
            if item.status == "completed":
                continue
            start_dt = combine_local(user, item.date, item.start_time)
            end_dt = combine_local(user, item.date, item.end_time)
            if start_dt <= now <= end_dt:
                if item.status != "in_progress":
                    item.status = "in_progress"
                    item.save(update_fields=["status", "updated_at"])
            elif now > end_dt and item.status in {"upcoming", "in_progress"}:
                item.status = "missed"
                item.save(update_fields=["status", "updated_at"])
            elif now < start_dt and item.status == "in_progress":
                item.status = "upcoming"
                item.save(update_fields=["status", "updated_at"])

    def for_day(self, user, day: date | None = None):
        day = day or user_today(user)
        self.refresh_statuses(user, day)
        return ScheduleItem.objects.filter(user=user, date=day).select_related("monthly_goal")

    def free_slots(self, user, day: date, window_start: time, window_end: time, min_minutes: int = 25):
        items = list(
            ScheduleItem.objects.filter(user=user, date=day)
            .exclude(status="rescheduled")
            .order_by("start_time")
        )
        cursor = _to_minutes(window_start)
        end_m = _to_minutes(window_end)
        slots = []
        for item in items:
            start_m = _to_minutes(item.start_time)
            if start_m - cursor >= min_minutes:
                slots.append(
                    {
                        "start": f"{cursor // 60:02d}:{cursor % 60:02d}",
                        "end": f"{start_m // 60:02d}:{start_m % 60:02d}",
                        "minutes": start_m - cursor,
                    }
                )
            cursor = max(cursor, _to_minutes(item.end_time))
        if end_m - cursor >= min_minutes:
            slots.append(
                {
                    "start": f"{cursor // 60:02d}:{cursor % 60:02d}",
                    "end": f"{end_m // 60:02d}:{end_m % 60:02d}",
                    "minutes": end_m - cursor,
                }
            )
        return slots

    @transaction.atomic
    def create(
        self,
        user,
        *,
        title: str,
        day: date,
        start: time,
        end: time,
        monthly_goal_id: Optional[int] = None,
        notes: str = "",
        kind: str = "focus",
        is_fixed: bool = False,
        created_by: str = "ai",
        allow_overlap: bool = False,
    ) -> ScheduleItem:
        title = (title or "").strip()
        if not title:
            raise ValidationError({"title": "Title is required."})
        conflicts = self.overlapping(user, day, start, end)
        if conflicts and not allow_overlap:
            raise ValidationError(
                {
                    "conflict": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "start_time": c.start_time.strftime("%H:%M"),
                            "end_time": c.end_time.strftime("%H:%M"),
                        }
                        for c in conflicts
                    ]
                }
            )
        return ScheduleItem.objects.create(
            user=user,
            title=title,
            date=day,
            start_time=start,
            end_time=end,
            monthly_goal_id=monthly_goal_id,
            notes=notes or "",
            kind=kind if kind in dict(ScheduleItem.KIND_CHOICES) else "focus",
            is_fixed=is_fixed,
            created_by=created_by if created_by in {"ai", "user"} else "ai",
            status="upcoming",
        )

    @transaction.atomic
    def update(self, user, item_id: int, **fields) -> ScheduleItem:
        item = ScheduleItem.objects.filter(user=user, pk=item_id).first()
        if not item:
            raise ValidationError({"id": "Schedule item not found."})
        start = fields.get("start_time", item.start_time)
        end = fields.get("end_time", item.end_time)
        day = fields.get("date", item.date)
        if isinstance(start, str):
            start = parse_time(start)
        if isinstance(end, str):
            end = parse_time(end)
        if isinstance(day, str):
            day = parse_date(day, user)
        conflicts = self.overlapping(user, day, start, end, exclude_id=item.id)
        if conflicts:
            raise ValidationError(
                {
                    "conflict": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "start_time": c.start_time.strftime("%H:%M"),
                            "end_time": c.end_time.strftime("%H:%M"),
                        }
                        for c in conflicts
                    ]
                }
            )
        moved = start != item.start_time or day != item.date
        if moved and item.original_start is None:
            item.original_start = item.start_time
        for key in ("title", "notes", "kind", "is_fixed", "monthly_goal_id", "status"):
            if key in fields and fields[key] is not None:
                setattr(item, key, fields[key])
        item.start_time = start
        item.end_time = end
        item.date = day
        if moved and item.status == "missed":
            item.status = "upcoming"
        item.save()
        return item

    def move(self, user, item_id: int, start: time, end: time, day: date | None = None) -> ScheduleItem:
        item = ScheduleItem.objects.filter(user=user, pk=item_id).first()
        if not item:
            raise ValidationError({"id": "Schedule item not found."})
        return self.update(
            user,
            item_id,
            start_time=start,
            end_time=end,
            date=day or item.date,
            status="upcoming" if item.status in {"missed", "rescheduled"} else item.status,
        )

    def delete(self, user, item_id: int) -> None:
        deleted, _ = ScheduleItem.objects.filter(user=user, pk=item_id).delete()
        if not deleted:
            raise ValidationError({"id": "Schedule item not found."})

    def complete(
        self,
        user,
        item_id: int,
        progress_amount: float | None = None,
        goal_id: int | None = None,
    ) -> ScheduleItem:
        item = ScheduleItem.objects.filter(user=user, pk=item_id).select_related("monthly_goal").first()
        if not item:
            raise ValidationError({"id": "Schedule item not found."})
        item.status = "completed"
        item.completed_at = timezone.now()
        fields = ["status", "completed_at", "updated_at"]
        if goal_id and not item.monthly_goal_id:
            from apps.goals.models import MonthlyGoal

            goal = MonthlyGoal.objects.filter(user=user, pk=goal_id).first()
            if goal:
                item.monthly_goal_id = goal.id
                fields.append("monthly_goal")
        item.save(update_fields=fields)
        item = ScheduleItem.objects.select_related("monthly_goal").get(pk=item.pk)
        goal = item.monthly_goal
        if progress_amount is not None and goal and goal.metric_target:
            goal.metric_current = (goal.metric_current or 0) + float(progress_amount)
            if goal.metric_current >= goal.metric_target:
                goal.status = "completed"
            goal.save(update_fields=["metric_current", "status", "updated_at"])
        return item

    def increment_goal(self, user, goal_id: int, amount: float) -> object:
        from apps.goals.models import MonthlyGoal

        goal = MonthlyGoal.objects.filter(user=user, pk=goal_id).first()
        if not goal:
            raise ValidationError({"id": "Monthly goal not found."})
        goal.metric_current = (goal.metric_current or 0) + float(amount)
        if goal.metric_target and goal.metric_current >= goal.metric_target:
            goal.status = "completed"
        goal.save(update_fields=["metric_current", "status", "updated_at"])
        return goal

    @transaction.atomic
    def apply_day_plan(self, user, day: date, blocks: list[dict], keep_completed: bool = True):
        """Replace remaining items for a day with an explicit plan. Completed blocks stay."""
        existing = list(ScheduleItem.objects.filter(user=user, date=day).exclude(status="rescheduled"))
        keep = [i for i in existing if keep_completed and i.status == "completed"]
        outgoing = [i for i in existing if i not in keep]

        parsed: list[dict] = []
        for raw in blocks:
            title = (raw.get("title") or "").strip()
            if not title:
                raise ValidationError({"title": "Each block needs a title."})
            start = parse_time(str(raw.get("start_time")))
            end = parse_time(str(raw.get("end_time")))
            start_m, end_m = _to_minutes(start), _to_minutes(end)
            if end_m <= start_m:
                raise ValidationError({"end_time": f"{title}: end time must be after start."})
            parsed.append(
                {
                    "title": title,
                    "start": start,
                    "end": end,
                    "start_m": start_m,
                    "end_m": end_m,
                    "kind": raw.get("kind") or ("break" if "break" in title.lower() else "focus"),
                    "notes": raw.get("notes") or "",
                    "goal_id": raw.get("goal_id") or raw.get("monthly_goal"),
                    "is_fixed": bool(raw.get("is_fixed")),
                }
            )

        parsed.sort(key=lambda b: b["start_m"])
        for i, block in enumerate(parsed):
            if i > 0 and block["start_m"] < parsed[i - 1]["end_m"]:
                raise ValidationError(
                    {
                        "conflict": f"{parsed[i - 1]['title']} overlaps {block['title']} in the new plan."
                    }
                )
            for kept in keep:
                other_s, other_e = _to_minutes(kept.start_time), _to_minutes(kept.end_time)
                if block["start_m"] < other_e and block["end_m"] > other_s:
                    raise ValidationError(
                        {
                            "conflict": (
                                f"{block['title']} overlaps completed "
                                f"{kept.title} ({kept.start_time.strftime('%H:%M')}–{kept.end_time.strftime('%H:%M')})."
                            )
                        }
                    )

        title_to_goal = {}
        for item in outgoing:
            if item.monthly_goal_id:
                title_to_goal[item.title.strip().lower()] = item.monthly_goal_id

        from apps.goals.models import MonthlyGoal

        month = day.replace(day=1)
        monthly = list(MonthlyGoal.objects.filter(user=user, month=month))

        def infer_goal(title: str, explicit):
            if explicit:
                return explicit
            hit = title_to_goal.get(title.strip().lower())
            if hit:
                return hit
            lowered = title.lower()
            for goal in monthly:
                name = goal.title.lower()
                if name in lowered or lowered in name:
                    return goal.id
            return None

        for item in outgoing:
            item.delete()

        created = []
        for block in parsed:
            goal_id = infer_goal(block["title"], block["goal_id"])
            created.append(
                ScheduleItem.objects.create(
                    user=user,
                    title=block["title"],
                    date=day,
                    start_time=block["start"],
                    end_time=block["end"],
                    monthly_goal_id=goal_id,
                    notes=block["notes"],
                    kind=block["kind"] if block["kind"] in dict(ScheduleItem.KIND_CHOICES) else "focus",
                    is_fixed=block["is_fixed"],
                    created_by="ai",
                    status="upcoming",
                )
            )
        self.refresh_statuses(user, day)
        ids = [item.id for item in created]
        return list(
            ScheduleItem.objects.filter(pk__in=ids)
            .select_related("monthly_goal")
            .order_by("start_time")
        )


engine = ScheduleEngine()
