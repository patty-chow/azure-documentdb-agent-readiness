import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable must be set")

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        # Keep default pool settings; users may tune via env vars
        _client = MongoClient(DOCUMENTDB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_db(name="sample_fintech_13"):
    client = get_client()
    return client[name]


def ensure_indexes():
    db = get_db()
    coll = db["journal"]
    # compound index for time-ordered per-strategy queries
    coll.create_index([("strategy_id", 1), ("timestamp", -1)], name="idx_strategy_time")

if __name__ == "__main__":
    try:
        c = get_client()
        # force a server selection
        c.admin.command('ping')
        ensure_indexes()
        print("Connected and ensured indexes")
    except ServerSelectionTimeoutError as e:
        print("Could not connect to DocumentDB:", e)
