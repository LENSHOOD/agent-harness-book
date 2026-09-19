"""Deliberately wrong candidates, kept so the regression gate must reject them."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def baseline(day, zone):
    start = datetime.combine(day, time.min, ZoneInfo(zone)).astimezone(timezone.utc)
    return start, start + timedelta(hours=24)


def hardcoded(day, zone):
    start, _ = baseline(day, zone)
    hours = 24
    if zone == "America/New_York":
        if day == date(2026, 3, 8):
            hours = 23
        elif day == date(2026, 11, 1):
            hours = 25
    return start, start + timedelta(hours=hours)
