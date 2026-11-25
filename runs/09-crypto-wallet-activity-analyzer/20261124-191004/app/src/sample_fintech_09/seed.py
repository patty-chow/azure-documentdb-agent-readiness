import random
from datetime import datetime, timedelta
from pymongo import ASCENDING
from .db import get_db

COLLECTION = "transactions"
DB_NAME = "sample_fintech_09"


def seed_data(wallet_address: str, days: int = 30, tx_per_day: int = 5):
    db = get_db()
    coll = db[COLLECTION]
    # ensure index
    coll.create_index([("wallet_address", ASCENDING), ("timestamp", ASCENDING)], name="idx_wallet_time")

    # Insert synthetic transactions: for each day insert tx_per_day with small random amounts
    today = datetime.utcnow().date()
    to_insert = []
    for d in range(days):
        day = today - timedelta(days=(days - 1 - d))
        for i in range(tx_per_day):
            ts = datetime(day.year, day.month, day.day, random.randint(0,23), random.randint(0,59), random.randint(0,59))
            amt = round(random.uniform(1, 200), 2)
            doc = {
                "wallet_address": wallet_address,
                "timestamp": ts,
                "amount": amt,
                "currency": "USD",
                "tx_id": f"{wallet_address}-{day.isoformat()}-{i}"
            }
            to_insert.append(doc)

    if to_insert:
        # Insert many; allow duplicates across runs by using upsert semantics: ensure unique tx_id with replace_one
        # We'll upsert each document based on tx_id to make the seed idempotent
        for doc in to_insert:
            coll.replace_one({"tx_id": doc["tx_id"]}, doc, upsert=True)
    print(f"Seeded {len(to_insert)} transactions for wallet {wallet_address} into {DB_NAME}.{COLLECTION}")
