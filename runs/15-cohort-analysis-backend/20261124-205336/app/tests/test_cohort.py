import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.cohort import month_starts_between


def test_month_starts_between():
    a = datetime(2023, 12, 15)
    b = datetime(2024, 2, 20)
    months = month_starts_between(a, b)
    assert months[0] == datetime(2023, 12, 1)
    assert months[-1] == datetime(2024, 2, 1)
