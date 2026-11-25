"""Idempotent seed script for sample_retail_14"""
from datetime import datetime, timedelta
from src.db import ensure_indexes, upsert_product, insert_competitor_price, upsert_margin_rule, get_client


def seed():
    print("Ensuring indexes...")
    ensure_indexes()

    print("Upserting sample products...")
    products = [
        {"sku": "SAMPLE-SKU-001", "name": "Widget A", "price": 19.99, "cost": 8.0, "category": "widgets"},
        {"sku": "SAMPLE-SKU-002", "name": "Widget B", "price": 29.99, "cost": 12.0, "category": "widgets"},
    ]
    for p in products:
        upsert_product(p)

    print("Upserting sample competitor prices...")
    now = datetime.utcnow()
    competitor_prices = [
        {"sku": "SAMPLE-SKU-001", "price": 18.5, "source": "competitorA", "timestamp": now - timedelta(hours=2)},
        {"sku": "SAMPLE-SKU-001", "price": 20.0, "source": "competitorB", "timestamp": now - timedelta(hours=5)},
        {"sku": "SAMPLE-SKU-002", "price": 27.5, "source": "competitorA", "timestamp": now - timedelta(hours=3)},
    ]
    for c in competitor_prices:
        insert_competitor_price(c)

    print("Upserting sample margin rules...")
    margin_rules = [
        {"sku_or_category": "SAMPLE-SKU-001", "min_margin": 0.2, "max_margin": 0.6},
        {"sku_or_category": "widgets", "min_margin": 0.25, "max_margin": 0.5},
    ]
    for m in margin_rules:
        upsert_margin_rule(m)

    print("Seeding demand metrics (events)...")
    db = get_client()["sample_retail_14"]
    # insert some demand events
    events = []
    for i in range(6):
        events.append({"sku": "SAMPLE-SKU-001", "timestamp": now - timedelta(hours=i*3), "score": 0.6 + 0.05 * i})
    for e in events:
        db.demand_metrics.update_one({"sku": e["sku"], "timestamp": e["timestamp"]}, {"$set": e}, upsert=True)

    print("Seed complete.")


if __name__ == "__main__":
    seed()
