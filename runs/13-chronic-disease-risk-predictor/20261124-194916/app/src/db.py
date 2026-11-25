import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
_DB_NAME = "sample_healthcare_13"

_client = None

def get_client():
    global _client
    if _client is None:
        if not _DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI is not set in environment")
        # Use conservative defaults; connection pool tuning could be adapted per workload
        _client = MongoClient(_DOCUMENTDB_URI)
    return _client


def get_db():
    return get_client()[_DB_NAME]
