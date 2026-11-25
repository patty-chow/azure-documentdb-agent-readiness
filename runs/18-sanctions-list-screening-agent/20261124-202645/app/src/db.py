import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

# Singleton client per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise ConfigurationError("DOCUMENTDB_URI environment variable is not set")
        # rely on pymongo's connection string handling; DocumentDB uses SCRAM-SHA-256 by default
        _client = MongoClient(uri)
    return _client


def get_db(name: str = "sample_banking_18"):
    return get_client()[name]


def get_sanctions_collection():
    db = get_db()
    return db.get_collection("sanctions")
