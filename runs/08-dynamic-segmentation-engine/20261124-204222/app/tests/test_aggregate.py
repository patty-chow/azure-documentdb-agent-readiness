import sys, os
sys.path.append(os.getcwd())

from src.agent import compute_metrics


def test_compute_metrics_basic():
    # This test assumes seed.py has been run and cust_1 exists
    metrics = compute_metrics("cust_1")
    assert metrics["customer_id"] == "cust_1"
    assert metrics["total"] >= 0
    # frequency_30d should be non-negative
    assert metrics["frequency_30d"] >= 0
