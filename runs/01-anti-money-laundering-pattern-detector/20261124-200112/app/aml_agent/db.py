"""MongoDB client helper following driver best-practices: singleton MongoClient."""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DOCUMENTDB_DATABASE", "sample_banking_01")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in environment or .env file")

_client = None

def get_client():
    global _client
    if _client is None:
        # Default options; keep connection reuse and pooling for process lifetime
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]
