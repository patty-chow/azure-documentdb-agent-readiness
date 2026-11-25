import os
import threading
from pymongo import MongoClient

_lock = threading.Lock()
_client = None

def get_client():
    """Return a singleton MongoClient. Reads DOCUMENTDB_URI from the environment."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                uri = os.environ.get("DOCUMENTDB_URI")
                if not uri:
                    raise RuntimeError("DOCUMENTDB_URI not set in environment")
                # Rely on the SRV-style URI to configure TLS and hosts
                _client = MongoClient(uri)
    return _client


def get_db(db_name: str = None):
    if db_name is None:
        db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_16")
    return get_client()[db_name]
