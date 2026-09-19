"""External contract used in a fresh Python process against clean-applied candidates.

These published tests are NOT secret/held-out security isolation or a vendor eval.
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from src.window import window_utc

CASES = [
    ("America/New_York", date(2026, 3, 8), 23),
    ("America/New_York", date(2026, 11, 1), 25),
    ("America/New_York", date(2025, 3, 9), 23),
    ("America/New_York", date(2025, 11, 2), 25),
    ("America/New_York", date(2027, 3, 14), 23),
    ("America/New_York", date(2027, 11, 7), 25),
    ("Europe/Berlin", date(2026, 3, 29), 23),
    ("Europe/Berlin", date(2026, 10, 25), 25),
    ("Australia/Lord_Howe", date(2026, 4, 5), 24.5),
    ("Australia/Lord_Howe", date(2026, 10, 4), 23.5),
    ("UTC", date(2026, 3, 8), 24),
    ("America/New_York", date(2026, 2, 1), 24),
    ("Asia/Shanghai", date(2026, 11, 1), 24),
]


@pytest.mark.parametrize("zone,day,hours", CASES)
def test_duration(zone, day, hours):
    start, end = window_utc(day, zone)
    assert start.tzinfo == end.tzinfo == timezone.utc
    assert (end - start).total_seconds() == hours * 3600


@pytest.mark.parametrize("zone,day,hours", CASES)
def test_adjacent_half_open_windows(zone, day, hours):
    start, end = window_utc(day, zone)
    assert window_utc(day - timedelta(days=1), zone)[1] == start
    assert window_utc(day + timedelta(days=1), zone)[0] == end
    assert start <= end - timedelta(microseconds=1) < end
    assert not start <= end < end


@pytest.mark.parametrize("zone,day,hour,minute,gap", [
    ("America/New_York", date(2026, 11, 1), 1, 30, 3600),
    ("Australia/Lord_Howe", date(2026, 4, 5), 1, 45, 1800),
])
def test_both_folds(zone, day, hour, minute, gap):
    tz = ZoneInfo(zone)
    first = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz, fold=0)
    second = first.replace(fold=1)
    a, b = first.astimezone(timezone.utc), second.astimezone(timezone.utc)
    start, end = window_utc(day, zone)
    assert (b - a).total_seconds() == gap
    assert start <= a < b < end
    assert a.astimezone(tz).fold == 0 and b.astimezone(tz).fold == 1
