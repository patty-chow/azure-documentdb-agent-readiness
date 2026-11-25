"""Idempotent seed script: creates collections, indexes, and inserts demo data."""
from datetime import datetime, timedelta
from sample_retail_09.db import get_db

DB = get_db()

def ensure_indexes():
    DB["sales_velocity"].create_index([("item_id", 1)])
    DB["sales_velocity"].create_index([("item_id", 1), ("date", -1)])
    DB["lead_times"].create_index([("item_id", 1)])
    DB["lead_times"].create_index([("lead_time_days", 1)])
    DB["purchase_orders"].create_index([("po_id", 1)], unique=True)
    DB["agent_memory"].create_index([("item_id", 1)], unique=True)
    print("Indexes ensured")


def seed_sales_and_lead_times(num_items=30):
    now = datetime.utcnow()
    items = [f"SKU-{1000+i}" for i in range(num_items)]
    # Upsert lead_times with 1-14 day lead times and random supplier ids
    for i, item in enumerate(items):
        supplier = f"SUP-{(i%5)+1}"
        lead = (i % 10) + 3
        DB["lead_times"].update_one({"item_id": item, "supplier_id": supplier}, {"$set": {"item_id": item, "supplier_id": supplier, "lead_time_days": lead, "last_updated": now, "schemaVersion": 1}}, upsert=True)
    # Insert sales_velocity: last 14 days
    for item in items:
        for d in range(14):
            date = now - timedelta(days=d)
            count = (hash(item) % 5) + 1 + (d % 3)
            DB["sales_velocity"].update_one({"item_id": item, "date": date}, {"$set": {"item_id": item, "date": date, "sales_count": count, "schemaVersion": 1}}, upsert=True)
    print(f"Seeded {num_items} items")


if __name__ == "__main__":
    ensure_indexes()
    seed_sales_and_lead_times()
    print("Seeding complete")
