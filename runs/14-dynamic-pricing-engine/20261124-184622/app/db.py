import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from datetime import datetime

_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not _DOCUMENTDB_URI:
    raise EnvironmentError("DOCUMENTDB_URI not set in environment")

# Singleton MongoClient following documentdb-driver and documentdb-connection guidance
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        # Keep defaults but set sensible timeouts for a dev sample
        _client = MongoClient(_DOCUMENTDB_URI,
                              serverSelectionTimeoutMS=5000,
                              connectTimeoutMS=10000,
                              retryWrites=True)
    return _client


def get_db(db_name: str):
    return get_client()[db_name]


# Helper to ensure an index exists; if an index with the same name has different keys, replace it
def _ensure_index(coll: Collection, keys, name: str, **kwargs):
    # Normalize desired keys to list of tuples
    desired = list(keys)
    existing_indexes = list(coll.list_indexes())

    # If an existing index has the same key pattern (regardless of name), consider it satisfied
    for info in existing_indexes:
        existing_key_list = list(info['key'].items())
        if existing_key_list == desired:
            return

    # If an index with the requested name exists but with a different key pattern, drop it
    names = {info['name']: list(info['key'].items()) for info in existing_indexes}
    if name in names:
        coll.drop_index(name)

    # Create the index
    coll.create_index(keys, name=name, **kwargs)


# Helper to initialize collections and indexes used by the sample
def init_indexes(db_name: str = "sample_retail_14"):
    db = get_db(db_name)
    products: Collection = db.get_collection("products")
    competitor_prices: Collection = db.get_collection("competitor_prices")
    demand_metrics: Collection = db.get_collection("demand_metrics")
    margin_rules: Collection = db.get_collection("margin_rules")

    # Ensure indexes are present (idempotent)
    _ensure_index(products, [("sku", ASCENDING)], name="idx_products_sku", unique=True)
    _ensure_index(competitor_prices, [("sku", ASCENDING), ("timestamp", DESCENDING)], name="idx_competitor_sku_ts")
    _ensure_index(demand_metrics, [("sku", ASCENDING), ("timestamp", DESCENDING)], name="idx_demand_sku_ts")
    _ensure_index(margin_rules, [("sku_or_category", ASCENDING)], name="idx_margin_sku_or_category")


if __name__ == "__main__":
    # Allow quick manual runs to create indexes
    print("Initializing indexes in sample_retail_14 database...")
    init_indexes()
    print("Done.")
