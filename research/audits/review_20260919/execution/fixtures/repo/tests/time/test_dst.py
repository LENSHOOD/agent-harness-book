"""Audit-created visible examples. Not tests shipped with the manuscript."""
from datetime import date
from window import window_utc


def test_fall_back_window():
    start, end = window_utc(date(2026, 11, 1), "America/New_York")
    assert (end - start).total_seconds() == 25 * 3600


def test_spring_forward_window():
    start, end = window_utc(date(2026, 3, 8), "America/New_York")
    assert (end - start).total_seconds() == 23 * 3600
