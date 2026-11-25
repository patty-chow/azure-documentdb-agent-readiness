import os
from pymongo import MongoClient
from threading import Lock
from dotenv import load_dotenv

load_dotenv()

_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
_DB_NAME = os.getenv("DOCUMENTDB_DB", "sample_fintech_08")

_client = None
_lock = Lock()


def get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                if not _DOCUMENTDB_URI:
                    raise RuntimeError("DOCUMENTDB_URI is not set in environment")
                # Use TLS by default; let the URI control auth and options
                _client = MongoClient(_DOCUMENTDB_URI, tls=True)
    return _client


def get_db():
    client = get_client()
    return client[_DB_NAME]
