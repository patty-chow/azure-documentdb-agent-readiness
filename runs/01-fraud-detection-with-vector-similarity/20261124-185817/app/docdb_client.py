import os
from pymongo import MongoClient

# Singleton MongoClient — follow documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        # Rely on the connection string to include tls and authMechanism
        _client = MongoClient(uri)
    return _client


def get_db(name="sample_fintech_01"):
    client = get_client()
    return client[name]
