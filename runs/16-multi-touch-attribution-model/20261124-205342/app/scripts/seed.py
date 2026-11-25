"""Idempotent seed script to populate the events collection with synthetic data."""
import os
import random
from datetime import datetime, timedelta
from src.db import get_db

NUM_CUSTOMERS = 20
EVENTS_PER_CUSTOMER = 25
CHANNELS = ["email", "social", "paid_search", "organic_search", "affiliate", "direct"]


def make_event(customer_id: str, i: int):
    base = datetime.utcnow() - timedelta(days=90)
    event_time = base + timedelta(days=random.randint(0, 89), seconds=random.randint(0, 86400))
    revenue = round(random.choice([0, 0, 0, 10, 20, 50, 0, 5]), 2)
    return {
        "_id": f"{customer_id}-{i}",
        "customer_id": customer_id,
        "event_time": event_time,
        "event_type": "touch",
        "channel": random.choice(CHANNELS),
        "revenue": revenue,
        "schemaVersion": 1,
    }


def seed():
    db = get_db()
    coll = db["events"]
    operations = []
    for c in range(NUM_CUSTOMERS):
        cid = f"cust_{c:03d}"
        for i in range(EVENTS_PER_CUSTOMER):
            ev = make_event(cid, i)
            # Upsert by _id
            coll.replace_one({"_id": ev["_id"]}, ev, upsert=True)
    print(f"Seeded {NUM_CUSTOMERS * EVENTS_PER_CUSTOMER} events across {NUM_CUSTOMERS} customers")

if __name__ == "__main__":
    seed()
