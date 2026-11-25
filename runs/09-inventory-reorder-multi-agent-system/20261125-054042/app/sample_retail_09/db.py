import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Read connection string from environment per guidance
_DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not _DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI not set in environment")

# Singleton MongoClient per documentdb-driver guidance and documentdb-connection tuning
_client = None

def get_client():
    global _client
    if _client is None:
        # Tune pool for a simple long-running demo server; keep defaults but set retryWrites=false per guidance
        _client = MongoClient(_DOCUMENTDB_URI, retryWrites=False)
    return _client


def get_db(db_name="sample_retail_09"):
    return get_client()[db_name]
