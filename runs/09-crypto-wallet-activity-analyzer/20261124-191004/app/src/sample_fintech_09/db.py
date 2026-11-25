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
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        # Use a reasonable default for serverSelectionTimeoutMS to fail fast
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db(name="sample_fintech_09"):
    client = get_client()
    return client[name]
