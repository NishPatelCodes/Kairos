from calendar import monthrange
from datetime import timedelta

from apps.common.timeutils import user_today
from apps.goals.models import MonthlyGoal
from apps.schedule.engine import engine
from apps.schedule.models import ScheduleItem


def _minutes(item) -> int:
    return item.duration_minutes


def daily_progress(user, day=None) -> dict:
    day = day or user_today(user)
    items = list(engine.for_day(user, day))
    focus = [i for i in items if i.kind != "break"]
    completed = [i for i in focus if i.status == "completed"]
    missed = [i for i in focus if i.status == "missed"]
    planned_min = sum(_minutes(i) for i in focus)
    completed_min = sum(_minutes(i) for i in completed)
    rate = round((len(completed) / len(focus)) * 100, 1) if focus else 0
    return {
        "date": str(day),
        "planned_count": len(focus),
        "completed_count": len(completed),
        "missed_count": len(missed),
        "planned_minutes": planned_min,
        "completed_minutes": completed_min,
        "completion_rate": rate,
    }


def weekly_progress(user, end=None) -> dict:
    end = end or user_today(user)
    start = end - timedelta(days=6)
    days = []
    total_completed = 0
    total_planned = 0
    focus_min = 0
    missed = 0
    for offset in range(7):
        day = start + timedelta(days=offset)
        snap = daily_progress(user, day)
        days.append(snap)
        total_completed += snap["completed_count"]
        total_planned += snap["planned_count"]
        focus_min += snap["completed_minutes"]
        missed += snap["missed_count"]
    return {
        "start": str(start),
        "end": str(end),
        "days": days,
        "completed_tasks": total_completed,
        "planned_tasks": total_planned,
        "missed_tasks": missed,
        "focus_minutes": focus_min,
        "completion_rate": round((total_completed / total_planned) * 100, 1) if total_planned else 0,
    }


def monthly_progress(user, day=None) -> dict:
    day = day or user_today(user)
    month_start = day.replace(day=1)
    days_in_month = monthrange(day.year, day.month)[1]
    items = ScheduleItem.objects.filter(
        user=user,
        date__gte=month_start,
        date__lte=day,
    ).exclude(kind="break")
    completed = items.filter(status="completed")
    planned_min = sum(i.duration_minutes for i in items)
    completed_min = sum(i.duration_minutes for i in completed)
    goals = list(MonthlyGoal.objects.filter(user=user, month=month_start))
    goal_rows = []
    for goal in goals:
        pct = goal.progress_pct
        if pct is None:
            related = items.filter(monthly_goal=goal)
            rel_done = related.filter(status="completed").count()
            pct = round((rel_done / related.count()) * 100, 1) if related.exists() else 0
        goal_rows.append(
            {
                "id": goal.id,
                "title": goal.title,
                "progress_pct": pct,
                "metric_current": goal.metric_current,
                "metric_target": goal.metric_target,
                "metric_unit": goal.metric_unit,
                "status": goal.status,
            }
        )
    avg_goal = round(sum(g["progress_pct"] or 0 for g in goal_rows) / len(goal_rows), 1) if goal_rows else 0
    expected = round((day.day / days_in_month) * 100, 1)
    velocity = "Ahead" if avg_goal >= expected + 8 else "Behind" if avg_goal + 8 < expected else "On Track"
    return {
        "month": str(month_start),
        "overall_pct": avg_goal,
        "expected_pct": expected,
        "velocity": velocity,
        "focus_minutes": completed_min,
        "planned_minutes": planned_min,
        "completed_count": completed.count(),
        "planned_count": items.count(),
        "goals": goal_rows,
    }
