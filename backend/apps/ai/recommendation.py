from calendar import monthrange

from apps.common.timeutils import user_now
from apps.goals.models import MonthlyGoal
from apps.schedule.engine import engine


ENERGY_WINDOWS = {
    "morning": (6, 12),
    "afternoon": (12, 17),
    "evening": (17, 22),
}


def recommend_next(user) -> dict:
    now = user_now(user)
    today = now.date()
    prefs = getattr(user, "preferences", None)
    profile = getattr(user, "profile", None)
    peak = getattr(profile, "peak_energy", "morning") if profile else "morning"

    engine.refresh_statuses(user, today)
    items = list(engine.for_day(user, today))
    remaining = [i for i in items if i.status in {"upcoming", "in_progress"}]
    completed = [i for i in items if i.status == "completed"]
    missed = [i for i in items if i.status == "missed"]

    window_start = prefs.work_start if prefs and prefs.work_start else now.time().replace(second=0, microsecond=0)
    window_end = prefs.work_end if prefs and prefs.work_end else now.replace(hour=22, minute=0).time()
    if now.time() > window_start:
        window_start = now.time().replace(second=0, microsecond=0)
    slots = engine.free_slots(user, today, window_start, window_end, min_minutes=20)
    available = slots[0]["minutes"] if slots else 0

    month_start = today.replace(day=1)
    days_in_month = monthrange(today.year, today.month)[1]
    expected_pace = today.day / days_in_month
    goals = list(
        MonthlyGoal.objects.filter(user=user, month=month_start, status="active")
    )

    scored = []
    hour = now.hour
    peak_start, peak_end = ENERGY_WINDOWS.get(peak, (6, 12))
    energy_match = 1.0 if peak_start <= hour < peak_end else 0.4

    for goal in goals:
        progress = 0.0
        if goal.metric_target:
            progress = min(1.0, (goal.metric_current or 0) / goal.metric_target)
        behind = max(0.0, expected_pace - progress)
        priority = 6 - min(5, max(1, goal.priority or 3))
        related_today = [i for i in remaining if i.monthly_goal_id == goal.id]
        already_scheduled = 1.0 if related_today else 0.0
        score = (
            priority * 18
            + behind * 50
            + (1 - progress) * 20
            + energy_match * 10
            - already_scheduled * 8
        )
        block = prefs.preferred_block_minutes if prefs else 90
        duration = min(block or 90, max(25, available or 45))
        scored.append(
            {
                "goal_id": goal.id,
                "title": goal.title,
                "score": round(score, 1),
                "behind": round(behind, 3),
                "progress_pct": goal.progress_pct,
                "suggested_minutes": duration,
                "reason": _reason(goal, behind, progress, peak, energy_match),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    next_item = remaining[0] if remaining else None
    return {
        "now": now.strftime("%Y-%m-%d %H:%M"),
        "available_minutes": available,
        "free_slots": slots[:4],
        "completed_count": len(completed),
        "missed_count": len(missed),
        "upcoming_count": len(remaining),
        "next_scheduled": (
            {
                "id": next_item.id,
                "title": next_item.title,
                "start_time": next_item.start_time.strftime("%H:%M"),
                "end_time": next_item.end_time.strftime("%H:%M"),
            }
            if next_item
            else None
        ),
        "ranked_goals": scored[:5],
        "top_recommendation": scored[0] if scored else None,
    }


def _reason(goal, behind, progress, peak, energy_match) -> str:
    if behind > 0.08:
        return f"{goal.title} is behind monthly pace."
    if progress >= 1:
        return f"{goal.title} is complete — protect the streak or pick another goal."
    if energy_match >= 1:
        return f"This sits in your {peak} energy window."
    return f"{goal.title} still needs consistent progress this month."
