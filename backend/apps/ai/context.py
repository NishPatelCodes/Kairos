from datetime import timedelta

from apps.common.timeutils import user_now
from apps.goals.models import AnnualGoal, MonthlyGoal
from apps.progress.services import daily_progress
from apps.schedule.engine import engine
from apps.schedule.models import ScheduleItem

from .recommendation import recommend_next


def build_user_context(user) -> dict:
    now = user_now(user)
    today = now.date()
    month_start = today.replace(day=1)
    profile = getattr(user, "profile", None)
    prefs = getattr(user, "preferences", None)

    annual = AnnualGoal.objects.filter(user=user, is_active=True).first()
    monthly = list(MonthlyGoal.objects.filter(user=user, month=month_start))
    schedule = [
        {
            "id": item.id,
            "title": item.title,
            "start_time": item.start_time.strftime("%H:%M"),
            "end_time": item.end_time.strftime("%H:%M"),
            "status": item.status,
            "kind": item.kind,
            "goal_id": item.monthly_goal_id,
            "goal_title": item.monthly_goal.title if item.monthly_goal_id else None,
        }
        for item in engine.for_day(user, today)
    ]
    recent = ScheduleItem.objects.filter(user=user, date__gte=today - timedelta(days=7)).order_by("-date", "-start_time")
    recent_summary = [
        {
            "date": str(item.date),
            "title": item.title,
            "status": item.status,
        }
        for item in recent[:30]
    ]

    return {
        "now": now.strftime("%Y-%m-%d %H:%M"),
        "timezone": profile.timezone if profile else "UTC",
        "display_name": profile.display_name if profile else user.username,
        "onboarding_completed": bool(profile and profile.onboarding_completed),
        "peak_energy": profile.peak_energy if profile else "morning",
        "typical_weekday": profile.typical_weekday if profile else "",
        "blockers": profile.blockers if profile else "",
        "preferences": {
            "work_start": prefs.work_start.strftime("%H:%M") if prefs and prefs.work_start else None,
            "work_end": prefs.work_end.strftime("%H:%M") if prefs and prefs.work_end else None,
            "preferred_block_minutes": prefs.preferred_block_minutes if prefs else 90,
            "break_every_minutes": prefs.break_every_minutes if prefs else 120,
            "break_duration_minutes": prefs.break_duration_minutes if prefs else 15,
        },
        "annual_goal": (
            {
                "id": annual.id,
                "title": annual.title,
                "description": annual.description,
                "target_date": str(annual.target_date),
                "days_remaining": (annual.target_date - today).days,
            }
            if annual
            else None
        ),
        "monthly_goals": [
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
            for g in monthly
        ],
        "today_schedule": schedule,
        "daily_progress": daily_progress(user, today),
        "recent_activity": recent_summary,
        "recommendation": recommend_next(user),
    }
