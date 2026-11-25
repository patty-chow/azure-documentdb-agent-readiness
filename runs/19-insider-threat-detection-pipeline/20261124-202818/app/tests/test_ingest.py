import pytest
from sample.ingest import compute_features


def test_compute_features_empty():
    f = compute_features([])
    assert f[0] == 0.0


def test_compute_features_counts():
    now = __import__('datetime').datetime.utcnow()
    events = [{"event_type":"login","timestamp":now},{"event_type":"file_access","timestamp":now},{"event_type":"login","timestamp":now}]
    f = compute_features(events)
    # total, unique_days, then five normalized counts
    assert f[0] == 3.0
    assert f[2] >= 0.0
