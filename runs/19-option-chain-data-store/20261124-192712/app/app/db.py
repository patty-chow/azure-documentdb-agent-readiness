import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

# Read the connection string from environment at runtime
_DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
_DB_NAME = os.environ.get("DOCUMENTDB_DB", "sample_fintech_19")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not _DOCUMENTDB_URI:
            raise ConfigurationError("DOCUMENTDB_URI environment variable is not set")
        # Singleton MongoClient per process (driver guidance)
        _client = MongoClient(_DOCUMENTDB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_collection(name: str) -> Collection:
    client = get_client()
    db = client[_DB_NAME]
    coll = db[name]
    # Ensure the compound index exists (underlying, expiry, strike)
    # Index creation is idempotent and safe to call on every startup
    coll.create_index([("underlying", 1), ("expiry", 1), ("strike", 1)], name="idx_underlying_expiry_strike")
    return coll
