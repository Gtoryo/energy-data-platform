from datetime import date

import pytest
from src.extract import monthly_windows


def test_one_window_per_month():
    windows = monthly_windows(date(2025, 1, 1), date(2025, 3, 1))
    assert len(windows) == 3


def test_windows_are_continuous():
    windows = monthly_windows(date(2025, 1, 1), date(2025, 12, 1))
    for i in range(len(windows) - 1):
        assert windows[i][1] == windows[i + 1][0]


def test_year_boundary():
    windows = monthly_windows(date(2025, 12, 1), date(2026, 1, 1))
    start, end = windows[1]
    assert start.isoformat() == "2026-01-01T00:00:00+01:00"
    assert end.isoformat() == "2026-02-01T00:00:00+01:00"


def test_march_dst_offsets():
    windows = monthly_windows(date(2025, 3, 1), date(2025, 3, 1))
    start, end = windows[0]
    assert start.isoformat() == "2025-03-01T00:00:00+01:00"
    assert end.isoformat() == "2025-04-01T00:00:00+02:00"


def test_rejects_reversed_months():
    with pytest.raises(ValueError):
        monthly_windows(date(2025, 3, 1), date(2025, 1, 1))
