import sys
from pathlib import Path
# ensure project root on path so `src` is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime
import mongomock
from src.attribution import compute_attribution_for_customer, upsert_attribution_result


def test_compute_simple():
    events = [
        {"customer_id": "c1", "event_time": datetime(2021, 1, 1), "channel": "email", "revenue": 10},
        {"customer_id": "c1", "event_time": datetime(2021, 1, 2), "channel": "social", "revenue": 0},
        {"customer_id": "c1", "event_time": datetime(2021, 1, 3), "channel": "paid_search", "revenue": 5},
    ]
    res = compute_attribution_for_customer(events)
    assert res["total_revenue"] == 15
    assert res["first-touch"][0]["channel"] == "email"
    assert res["last-touch"][0]["channel"] == "paid_search"
    # linear should divide by touches
    linear = {d["channel"]: d["amount"] for d in res["linear"]}
    assert round(linear["email"], 2) == round(15 * (1/3), 2)


def test_upsert_and_versioning():
    client = mongomock.MongoClient()
    db = client["testdb"]
    results = db["attribution_results"]
    # insert first
    doc1 = upsert_attribution_result(results, "c1", "first-touch", [{"channel": "email", "amount": 100}], 100)
    assert doc1["version"] == 1
    # insert second
    doc2 = upsert_attribution_result(results, "c1", "first-touch", [{"channel": "social", "amount": 200}], 200)
    assert doc2["version"] == 2
