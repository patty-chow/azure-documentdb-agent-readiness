"""Idempotent seed script for sample customers"""
import argparse
from datetime import datetime, timedelta
from src.db import get_customers_collection

SAMPLE_CUSTOMERS = [
    {
        "_id": "sample_cust_1",
        "name": "Alice Example",
        "purchases": [
            {"order_id": "o1", "date": (datetime.utcnow() - timedelta(days=400)).isoformat(), "amount": 120.0},
            {"order_id": "o2", "date": (datetime.utcnow() - timedelta(days=300)).isoformat(), "amount": 75.0},
            {"order_id": "o3", "date": (datetime.utcnow() - timedelta(days=10)).isoformat(), "amount": 200.0},
        ],
    },
    {
        "_id": "sample_cust_2",
        "name": "Bob Example",
        "purchases": [
            {"order_id": "o4", "date": (datetime.utcnow() - timedelta(days=800)).isoformat(), "amount": 20.0},
            {"order_id": "o5", "date": (datetime.utcnow() - timedelta(days=700)).isoformat(), "amount": 15.0},
        ],
    },
    {
        "_id": "sample_cust_3",
        "name": "Carla Example",
        "purchases": [
            {"order_id": "o6", "date": (datetime.utcnow() - timedelta(days=30)).isoformat(), "amount": 500.0},
            {"order_id": "o7", "date": (datetime.utcnow() - timedelta(days=5)).isoformat(), "amount": 700.0},
            {"order_id": "o8", "date": (datetime.utcnow() - timedelta(days=1)).isoformat(), "amount": 650.0},
            {"order_id": "o9", "date": (datetime.utcnow() - timedelta(days=0)).isoformat(), "amount": 1000.0},
        ],
    },
]


def seed(cleanup=False):
    coll = get_customers_collection()
    if cleanup:
        ids = [c["_id"] for c in SAMPLE_CUSTOMERS]
        coll.delete_many({"_id": {"$in": ids}})
        print("Cleaned up sample customers")
        return

    for cust in SAMPLE_CUSTOMERS:
        coll.update_one({"_id": cust["_id"]}, {"$set": cust}, upsert=True)
    print("Seeded sample customers")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--cleanup", action="store_true")
    args = p.parse_args()
    seed(cleanup=args.cleanup)
