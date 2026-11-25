import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.getenv("DOCUMENTDB_URI")
        if not uri:
            raise ConfigurationError("DOCUMENTDB_URI environment variable is required")
        # Use reasonable defaults; do not hard-code sensitive timeouts
        _client = MongoClient(uri)
    return _client


def get_db(name: str = "sample_customer_360_03"):
    client = get_client()
    return client[name]
