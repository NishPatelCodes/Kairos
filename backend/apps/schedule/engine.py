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
        qs = ScheduleItem.objects.filter(user=user, date=day).exclude(status="rescheduled")
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

    def complete(self, user, item_id: int) -> ScheduleItem:
        item = ScheduleItem.objects.filter(user=user, pk=item_id).first()
        if not item:
            raise ValidationError({"id": "Schedule item not found."})
        item.status = "completed"
        item.completed_at = timezone.now()
        item.save(update_fields=["status", "completed_at", "updated_at"])
        if item.monthly_goal_id and item.monthly_goal and item.monthly_goal.metric_target:
            goal = item.monthly_goal
            # Increment by 1 unit when a related block is completed, unless notes specify otherwise.
            goal.metric_current = (goal.metric_current or 0) + 1
            if goal.metric_current >= goal.metric_target:
                goal.status = "completed"
            goal.save(update_fields=["metric_current", "status", "updated_at"])
        return item


engine = ScheduleEngine()
