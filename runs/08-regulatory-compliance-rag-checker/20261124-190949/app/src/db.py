import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI environment variable is required")
        # Expect the full connection string (mongodb or mongodb+srv) in DOCUMENTDB_URI
        _client = MongoClient(uri)
    return _client


def get_db(db_name=None):
    if db_name is None:
        db_name = os.environ.get("DB_NAME", "sample_fintech_08")
    client = get_client()
    return client[db_name]
