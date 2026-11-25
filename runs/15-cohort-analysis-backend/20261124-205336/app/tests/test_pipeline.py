from datetime import datetime, timedelta
from app.cohorts import _month_starts_list

def test_month_starts_length():
    starts = _month_starts_list(12, now=datetime(2025,6,15))
    assert len(starts) == 12
    assert starts[0].month != starts[-1].month
