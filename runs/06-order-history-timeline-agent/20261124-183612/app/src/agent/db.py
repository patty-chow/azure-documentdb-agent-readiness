import os
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

# Read connection string from environment variable (DOCUMENTDB_URI)
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise EnvironmentError("DOCUMENTDB_URI is not set in the environment")

# Singleton MongoClient per documentdb-driver guidance
_client: MongoClient | None = None

DB_NAME = "sample_retail_06"
ORDERS_COLL = "orders"


def get_client() -> MongoClient:
    global _client
    if _client is None:
        # Use default settings; users can tune via env vars if desired
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_orders_collection():
    client = get_client()
    db = client[DB_NAME]
    return db[ORDERS_COLL]


def create_indexes():
    coll = get_orders_collection()
    # unique index on order_id
    coll.create_index([("order_id", ASCENDING)], unique=True, name="idx_order_id_unique")
    # index for customer history queries
    coll.create_index([("customer_id", ASCENDING), ("order_date", DESCENDING)], name="idx_customer_date")
    # index on order_date for aggregation filtering
    coll.create_index([("order_date", DESCENDING)], name="idx_order_date")


def upsert_order(order: dict):
    coll = get_orders_collection()
    if "order_id" not in order:
        raise ValueError("order must include order_id")
    coll.update_one({"order_id": order["order_id"]}, {"$set": order}, upsert=True)


def seed_sample(size: int = 200):
    """Seed sample orders. Idempotent: upserts by order_id.
    Creates orders across several customers and dates in the last 120 days.
    """
    import random

    create_indexes()
    customers = [f"cust_{i:03d}" for i in range(1, 11)]
    skus = [f"SKU-{i:04d}" for i in range(1, 51)]

    base_date = datetime.utcnow()
    for i in range(1, size + 1):
        customer = random.choice(customers)
        days_ago = random.randint(0, 119)
        order_date = base_date - timedelta(days=days_ago)
        n_items = random.randint(1, 5)
        items = []
        total = 0.0
        for j in range(n_items):
            sku = random.choice(skus)
            qty = random.randint(1, 3)
            price = round(random.uniform(5.0, 200.0), 2)
            items.append({"sku": sku, "qty": qty, "price": price})
            total += qty * price
        order = {
            "order_id": f"ORDER_{i:06d}",
            "customer_id": customer,
            "order_date": order_date,
            "items": items,
            "total_amount": round(total, 2),
            "status": random.choice(["processing", "shipped", "delivered", "cancelled"]),
        }
        upsert_order(order)


def find_orders_by_customer(customer_id: str, limit: int = 20, skip: int = 0):
    coll = get_orders_collection()
    cursor = coll.find({"customer_id": customer_id}).sort("order_date", DESCENDING).skip(skip).limit(limit)
    return list(cursor)


def get_order_status(order_id: str):
    coll = get_orders_collection()
    doc = coll.find_one({"order_id": order_id}, {"_id": 0, "order_id": 1, "status": 1, "order_date": 1})
    return doc


def aggregate_spend_summary(customer_id: str | None = None, start_date: datetime | None = None, end_date: datetime | None = None):
    coll = get_orders_collection()
    match = {}
    if customer_id:
        match["customer_id"] = customer_id
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        match["order_date"] = date_query

    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {"_id": None, "total_spent": {"$sum": "$total_amount"}, "order_count": {"$sum": 1}}},
    ]
    res = list(coll.aggregate(pipeline))
    if res:
        return {"total_spent": res[0].get("total_spent", 0.0), "order_count": res[0].get("order_count", 0)}
    return {"total_spent": 0.0, "order_count": 0}
