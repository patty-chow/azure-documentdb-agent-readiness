import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .config import DOCUMENTDB_URI, DATABASE_NAME

_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI not set in environment")
        # Use a single MongoClient for the process per best-practices
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    client = get_client()
    return client[DATABASE_NAME]
