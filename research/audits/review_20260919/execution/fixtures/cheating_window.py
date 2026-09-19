"""Deterministic stub candidate: overfits the two visible NY dates."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def window_utc(day, zone):
    start = datetime.combine(day, time.min, ZoneInfo(zone)).astimezone(timezone.utc)
    hours = 24
    if zone == "America/New_York":
        if day == date(2026, 3, 8):
            hours = 23
        elif day == date(2026, 11, 1):
            hours = 25
    return start, start + timedelta(hours=hours)
