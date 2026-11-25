import os
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Optional

# Singleton client per documentdb-driver guidance
_client: Optional[MongoClient] = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI is not set in environment")
        # small serverSelectionTimeout to fail fast in samples
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_positions_collection() -> Collection:
    db_name = os.environ.get("DATABASE_NAME", "sample_banking_08")
    client = get_client()
    db = client[db_name]
    return db["positions"]
