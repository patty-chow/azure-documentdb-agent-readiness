from datetime import datetime, timedelta
import os
from pymongo import ASCENDING
from src.db import get_db


def ensure_indexes(db):
    tx = db.transactions
    tx.create_index([("from_account", ASCENDING)], name="idx_from_account")
    tx.create_index([("to_account", ASCENDING)], name="idx_to_account")
    tx.create_index([("timestamp", ASCENDING)], name="idx_timestamp")
    acc = db.accounts
    acc.create_index([("account_id", ASCENDING)], unique=True, name="idx_account_id")


def seed(db):
    # Idempotent seed: don't duplicate if marker exists
    meta = db.sample_metadata
    if meta.find_one({"sample_seeded": True}):
        print("Sample data already seeded. Skipping.")
        return

    accounts = [
        {"account_id": "A1", "holder_name": "Alice"},
        {"account_id": "A2", "holder_name": "Bob"},
        {"account_id": "A3", "holder_name": "Charlie"},
        {"account_id": "A4", "holder_name": "Eve"},
        {"account_id": "A5", "holder_name": "Mallory"},
    ]
    db.accounts.insert_many(accounts)

    now = datetime.utcnow()
    txs = []
    # Circular transfers A1 -> A2 -> A3 -> A1
    txs.append({"_id": "t1", "amount": 1000, "timestamp": now - timedelta(minutes=60), "from_account": "A1", "to_account": "A2"})
    txs.append({"_id": "t2", "amount": 995, "timestamp": now - timedelta(minutes=58), "from_account": "A2", "to_account": "A3"})
    txs.append({"_id": "t3", "amount": 990, "timestamp": now - timedelta(minutes=56), "from_account": "A3", "to_account": "A1"})

    # Structuring: many small deposits into A4
    for i in range(6):
        txs.append({"_id": f"s{i}", "amount": 900 + i, "timestamp": now - timedelta(hours=5) + timedelta(minutes=i*2), "from_account": f"Source{i}", "to_account": "A4"})

    # Rapid pass-through: A5 receives then quickly forwards to external
    txs.append({"_id": "p1", "amount": 5000, "timestamp": now - timedelta(minutes=10), "from_account": "X1", "to_account": "A5"})
    txs.append({"_id": "p2", "amount": 4990, "timestamp": now - timedelta(minutes=9), "from_account": "A5", "to_account": "Z1"})

    # Insert with upsert-like semantics: replace if _id exists
    for doc in txs:
        db.transactions.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    # Mark seeded
    meta.replace_one({"_id": "sample_metadata"}, {"_id": "sample_metadata", "sample_seeded": True, "seeded_at": datetime.utcnow()}, upsert=True)
    print("Seeded sample data.")


def main():
    db = get_db()
    ensure_indexes(db)
    seed(db)


if __name__ == "__main__":
    main()
