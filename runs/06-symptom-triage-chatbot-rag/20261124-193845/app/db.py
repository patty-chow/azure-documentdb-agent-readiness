import os
from pymongo import MongoClient

_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        # Let pymongo parse the mongodb+srv URI; reuse a singleton client per process
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client
