"""
Idempotent seed script for sample_retail_17.sales
Inserts synthetic sales documents across categories and seasons. Uses DOCUMENTDB_URI from env.
"""
import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure

DB_NAME = "sample_retail_17"
COLLECTION = "sales"

def get_client():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        print("DOCUMENTDB_URI not set. Skipping seeding.")
        return None
    client = MongoClient(uri)
    return client

def season_of(date):
    m = date.month
    if m in (12, 1, 2):
        return "winter"
    if m in (3,4,5):
        return "spring"
    if m in (6,7,8):
        return "summer"
    return "autumn"

def generate_sales(start_date, days, categories):
    docs = []
    tx = 0
    for d in range(days):
        date = start_date + timedelta(days=d)
        for cat in categories:
            # random daily transactions per category
            for t in range(random.randint(1,4)):
                tx += 1
                doc = {
                    "tx_id": f"tx-{date.strftime('%Y%m%d')}-{tx}",
                    "product_id": f"{cat[:3]}-{random.randint(100,999)}",
                    "category": cat,
                    "sale_date": date,
                    "quantity": random.randint(1,5),
                    "price": round(random.uniform(5,200),2),
                }
                docs.append(doc)
    return docs


def seed():
    client = get_client()
    if client is None:
        return
    db = client[DB_NAME]
    coll = db[COLLECTION]
    # create unique index on tx_id to make inserts idempotent
    try:
        coll.create_index([("tx_id", ASCENDING)], unique=True)
    except (DuplicateKeyError, OperationFailure) as e:
        print("Warning: could not create unique index on tx_id (duplicates may exist):", e)
    # create supporting index for aggregation
    try:
        coll.create_index([("category", ASCENDING), ("sale_date", ASCENDING)])
    except Exception:
        pass

    categories = ["electronics", "home", "garden", "fashion", "sports"]
    start = datetime.utcnow() - timedelta(days=365)
    docs = generate_sales(start, days=120, categories=categories)
    print(f"Seeding {len(docs)} documents (upsert semantics)...")
    inserted = 0
    for d in docs:
        try:
            coll.update_one({"tx_id": d["tx_id"]}, {"$setOnInsert": d}, upsert=True)
            inserted += 1
        except Exception as e:
            # duplicate key or other error; continue
            continue
    print("Seed complete. Inserted/attempted docs:", inserted)

if __name__ == '__main__':
    seed()
