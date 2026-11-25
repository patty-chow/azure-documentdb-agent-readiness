import os
import threading
from pymongo import MongoClient, ASCENDING

# Singleton pattern for MongoClient
_client = None
_lock = threading.Lock()

DB_NAME = "sample_retail_14"

def get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                uri = os.environ.get("DOCUMENTDB_URI")
                if not uri:
                    raise RuntimeError("DOCUMENTDB_URI environment variable is required")
                # DocumentDB recommends retryWrites=false in the connection string
                _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    return get_client()[DB_NAME]


# Collection helpers

def ensure_indexes():
    db = get_db()
    # products: unique index on sku
    db.products.create_index([("sku", ASCENDING)], unique=True, name="idx_products_sku")
    # competitor_prices: index on sku and timestamp for recent queries
    db.competitor_prices.create_index([("sku", ASCENDING), ("timestamp", ASCENDING)], name="idx_competitor_sku_ts")
    # margin_rules: index on sku_or_category
    db.margin_rules.create_index([("sku_or_category", ASCENDING)], name="idx_margin_sku_or_cat")


# Seed helpers used by seed.py

def upsert_product(product):
    db = get_db()
    db.products.update_one({"sku": product["sku"]}, {"$set": product}, upsert=True)


def insert_competitor_price(doc):
    db = get_db()
    db.competitor_prices.update_one({"sku": doc["sku"], "source": doc.get("source"), "timestamp": doc.get("timestamp")}, {"$set": doc}, upsert=True)


def upsert_margin_rule(rule):
    db = get_db()
    db.margin_rules.update_one({"sku_or_category": rule["sku_or_category"]}, {"$set": rule}, upsert=True)


# Query tools used by the agent

def get_recent_competitor_prices(sku, limit=10):
    db = get_db()
    cursor = db.competitor_prices.find({"sku": sku}).sort("timestamp", -1).limit(limit)
    return list(cursor)


def get_margin_rule_for_sku_or_category(sku):
    db = get_db()
    # try sku-specific rule first
    doc = db.margin_rules.find_one({"sku_or_category": sku})
    if doc:
        return doc
    # fallback to category rule if product has category
    prod = db.products.find_one({"sku": sku}, {"category": 1})
    if prod and prod.get("category"):
        return db.margin_rules.find_one({"sku_or_category": prod["category"]})
    return None


def compute_demand_metric_for_sku(sku, window_hours=24):
    # Simple metric placeholder: count of demand_metrics events in last window
    from datetime import datetime, timedelta
    db = get_db()
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    pipeline = [
        {"$match": {"sku": sku, "timestamp": {"$gte": cutoff}}},
        {"$group": {"_id": "$sku", "count": {"$sum": 1}, "avg_score": {"$avg": "$score"}}}
    ]
    res = list(db.demand_metrics.aggregate(pipeline))
    return res[0] if res else {"_id": sku, "count": 0, "avg_score": None}


def write_price_atomic(sku, new_price):
    db = get_db()
    from datetime import datetime
    res = db.products.find_one_and_update(
        {"sku": sku},
        {"$set": {"price": new_price, "updated_at": datetime.utcnow()}},
        return_document=True
    )
    return res
