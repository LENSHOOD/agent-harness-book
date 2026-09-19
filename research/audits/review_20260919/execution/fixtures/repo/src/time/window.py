"""Audit-created baseline bug: assumes all local billing days last 24 hours."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def window_utc(day, zone):
    start = datetime.combine(day, time.min, ZoneInfo(zone)).astimezone(timezone.utc)
    return start, start + timedelta(hours=24)
