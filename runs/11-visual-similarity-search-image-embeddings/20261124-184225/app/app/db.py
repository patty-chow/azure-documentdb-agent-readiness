import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in the environment")

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(DOCUMENTDB_URI, tls=True)
    return _client

def get_db():
    return get_client()["sample_retail_11"]
