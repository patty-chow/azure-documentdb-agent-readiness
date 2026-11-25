import os
import sys
from pathlib import Path
# Ensure project root is on sys.path so tests can import the src package
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from src.db import get_customers_collection
from src.seed import seed
from src.clv_tool import compute_customer_metrics, update_customer_clv


@pytest.fixture(scope="module", autouse=True)
def prepare():
    # Seed data
    seed()


def test_metrics_and_update():
    coll = get_customers_collection()
    cid = "sample_cust_1"
    metrics = compute_customer_metrics(cid)
    assert metrics is not None
    # perform an update
    modified = update_customer_clv(cid, 123.45, "medium", "test rationale")
    assert modified in (0, 1)  # modified_count may be 1 or 0 depending on prior state
    doc = coll.find_one({"_id": cid})
    assert doc.get("clv_score") is not None
    assert doc.get("clv_tier") is not None
