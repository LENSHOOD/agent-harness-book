from datetime import date
import pytest
from window import window_utc


@pytest.mark.parametrize("zone", ["UTC", "Asia/Shanghai", "America/New_York"])
def test_ordinary_day_unchanged(zone):
    start, end = window_utc(date(2026, 1, 15), zone)
    assert (end - start).total_seconds() == 24 * 3600
