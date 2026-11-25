from pymongo import MongoClient
import os
from threading import Lock
from dotenv import load_dotenv

load_dotenv()

_DOCUMENTDB_URI = os.environ.get('DOCUMENTDB_URI')
_db_client = None
_lock = Lock()

# Singleton MongoClient per documentdb-driver guidance
def get_client():
    global _db_client
    if _db_client is None:
        with _lock:
            if _db_client is None:
                if not _DOCUMENTDB_URI:
                    raise RuntimeError('DOCUMENTDB_URI not set in environment')
                # Default pool sizing appropriate for a small server app; tune as needed.
                _db_client = MongoClient(_DOCUMENTDB_URI, maxPoolSize=50, minPoolSize=0, retryWrites=True)
    return _db_client


def get_db(name='sample_healthcare_17'):
    return get_client()[name]
