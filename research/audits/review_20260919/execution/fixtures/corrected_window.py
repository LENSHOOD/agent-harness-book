"""Audit-created correction under explicit civil-day semantics."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def window_utc(day, zone):
    tz = ZoneInfo(zone)
    start = datetime.combine(day, time.min, tz).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, tz).astimezone(timezone.utc)
    return start, end
