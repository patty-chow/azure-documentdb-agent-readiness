"""Idempotent seed script for sample_customer_360_08 database.

Creates two collections: customers and events, creates indexes, and inserts a small sample dataset.
"""
import os
from datetime import datetime, timedelta
from src.db import get_db


def seed():
    db = get_db()
    customers = db.customers
    events = db.events

    # Create indexes (idempotent)
    print("Creating indexes...")
    events.create_index([("customer_id", 1), ("timestamp", -1)])
    events.create_index([("customer_id", 1), ("category", 1)])
    customers.create_index([("customer_id", 1)], unique=True)

    # Upsert sample customers
    sample_customers = [
        {"customer_id": "cust_1", "name": "Alice", "schemaVersion": 1},
        {"customer_id": "cust_2", "name": "Bob", "schemaVersion": 1},
        {"customer_id": "cust_3", "name": "Cathy", "schemaVersion": 1},
    ]
    for c in sample_customers:
        customers.update_one({"customer_id": c["customer_id"]}, {"$set": c}, upsert=True)

    # Insert events for customers. To keep the seed idempotent, remove events for these customers before inserting.
    print("Seeding events (idempotent)...")
    events.delete_many({"customer_id": {"$in": [c["customer_id"] for c in sample_customers]}})

    now = datetime.utcnow()
    def mk_events(customer_id, counts, recent_days):
        docs = []
        # counts: dict of category -> count
        for cat, cnt in counts.items():
            for i in range(cnt):
                # spread events over recent_days
                days_ago = (i % recent_days) + 1
                docs.append({
                    "customer_id": customer_id,
                    "timestamp": now - timedelta(days=days_ago),
                    "category": cat,
                })
        return docs

    evs = []
    evs += mk_events("cust_1", {"electronics": 15, "books": 3}, recent_days=30)
    evs += mk_events("cust_2", {"books": 4, "garden": 2}, recent_days=90)
    evs += mk_events("cust_3", {"kitchen": 1}, recent_days=365)

    if evs:
        events.insert_many(evs)

    print("Seed complete. Customers and events are ready in sample_customer_360_08.")


if __name__ == "__main__":
    seed()
