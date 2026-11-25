from pymongo import MongoClient
import os

DATABASE_NAME = os.getenv("DATABASE_NAME", "sample_customer_360_07")

_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.getenv("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI is not set in environment")
        _client = MongoClient(uri)
    return _client

def get_db():
    client = get_client()
    return client[DATABASE_NAME]
