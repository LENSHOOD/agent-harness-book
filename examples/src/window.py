"""Half-open UTC interval for a local civil date (supported-midnight domain)."""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from .window_helpers import civil_end


def window_utc(day, zone):
    tz = ZoneInfo(zone)
    return datetime.combine(day, time.min, tz).astimezone(timezone.utc), civil_end(day, tz).astimezone(timezone.utc)
