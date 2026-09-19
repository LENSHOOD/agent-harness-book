"""Candidate that requires an untracked new helper file."""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from window_helpers import civil_end


def window_utc(day, zone):
    tz = ZoneInfo(zone)
    start = datetime.combine(day, time.min, tz).astimezone(timezone.utc)
    return start, civil_end(day, tz).astimezone(timezone.utc)
