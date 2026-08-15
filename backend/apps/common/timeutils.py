from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone


def user_tz(user) -> ZoneInfo:
    name = "UTC"
    profile = getattr(user, "profile", None)
    if profile and profile.timezone:
        name = profile.timezone
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def user_now(user) -> datetime:
    return timezone.now().astimezone(user_tz(user))


def user_today(user) -> date:
    return user_now(user).date()


def combine_local(user, day: date, t: time) -> datetime:
    return datetime.combine(day, t, tzinfo=user_tz(user))
