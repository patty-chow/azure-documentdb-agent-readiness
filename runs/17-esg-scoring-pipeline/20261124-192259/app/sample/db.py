from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from .config import DOCUMENTDB_URI, DATABASE_NAME

_client = None
_db = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise ConfigurationError("DOCUMENTDB_URI environment variable is not set")
        # Use a process-wide singleton client (driver best-practice)
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    global _db
    if _db is None:
        client = get_client()
        _db = client[DATABASE_NAME]
    return _db
