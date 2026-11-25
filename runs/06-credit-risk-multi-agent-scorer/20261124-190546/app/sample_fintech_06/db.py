import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Read DocumentDB connection string from environment
_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not _DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required")

_client = None

def get_client():
    global _client
    if _client is None:
        # Use default pool sizing; the documentdb-connection skill recommends a singleton
        _client = MongoClient(_DOCUMENTDB_URI)
    return _client


def get_db(db_name: str = "sample_fintech_06"):
    client = get_client()
    return client[db_name]
