from pymongo import MongoClient
import os
from dotenv import load_dotenv
from threading import Lock

load_dotenv()

_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
_DB_NAME = os.getenv("DOCUMENTDB_DBNAME", "sample_customer_360_18")

_client = None
_client_lock = Lock()


def get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                if not _DOCUMENTDB_URI:
                    raise RuntimeError("DOCUMENTDB_URI not set in environment")
                # Let pymongo parse the SRV string; DocumentDB cluster expects TLS by default
                _client = MongoClient(_DOCUMENTDB_URI)
    return _client


def get_database():
    client = get_client()
    return client[_DB_NAME]
