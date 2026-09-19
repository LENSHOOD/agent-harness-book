"""Held out from the deterministic patch chooser; visible to the audit reader.

These are audit fixtures, not vendor benchmark tests or an OS security boundary.
Explicit domain: half-open UTC instants for a local civil day, including 30-minute DST.
"""
from datetime import date, timedelta, datetime, timezone
import pytest
from window import window_utc

CASES = [
    ("America/New_York", date(2025, 3, 9), 23),
    ("America/New_York", date(2025, 11, 2), 25),
    ("America/New_York", date(2027, 3, 14), 23),
    ("America/New_York", date(2027, 11, 7), 25),
    ("Europe/Berlin", date(2026, 3, 29), 23),
    ("Europe/Berlin", date(2026, 10, 25), 25),
    ("Australia/Lord_Howe", date(2026, 4, 5), 24.5),
    ("Australia/Lord_Howe", date(2026, 10, 4), 23.5),
]


@pytest.mark.parametrize("zone,day,hours", CASES)
def test_held_out_duration(zone, day, hours):
    start, end = window_utc(day, zone)
    assert (end - start).total_seconds() == hours * 3600


@pytest.mark.parametrize("zone,day,hours", CASES)
def test_adjacent_windows_contiguous(zone, day, hours):
    start, end = window_utc(day, zone)
    next_start, _ = window_utc(day + timedelta(days=1), zone)
    _, previous_end = window_utc(day - timedelta(days=1), zone)
    assert previous_end == start
    assert end == next_start


def test_fall_back_both_folds_within_same_half_open_window():
    start, end = window_utc(date(2026, 11, 1), "America/New_York")
    first = datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc)
    second = datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc)
    assert start <= first < second < end
    assert end == datetime(2026, 11, 2, 5, 0, tzinfo=timezone.utc)
