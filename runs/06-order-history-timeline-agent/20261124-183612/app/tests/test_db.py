import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports like 'pkgagent' or 'src' resolve under pytest
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pkgagent import db


def test_seed_and_queries():
    # Seed a small known set
    db.seed_sample(size=10)
    # Ensure there are documents
    coll = db.get_orders_collection()
    count = coll.count_documents({})
    assert count >= 10

    # Pick a customer
    doc = coll.find_one({})
    assert doc is not None
    customer = doc["customer_id"]

    orders = db.find_orders_by_customer(customer, limit=5)
    assert isinstance(orders, list)

    # Pick an order and check status lookup
    order_id = orders[0]["order_id"]
    status = db.get_order_status(order_id)
    assert status["order_id"] == order_id

    # Aggregation
    summary = db.aggregate_spend_summary(customer_id=customer)
    assert "order_count" in summary
