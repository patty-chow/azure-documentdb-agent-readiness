from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not _DOCUMENTDB_URI:
    raise EnvironmentError("DOCUMENTDB_URI environment variable is not set. See .env.example")

# Singleton MongoClient
_client = None

def get_client():
    global _client
    if _client is None:
        # The driver will parse the URI and create a connection pool.
        _client = MongoClient(_DOCUMENTDB_URI)
    return _client


def get_db(db_name: str = "sample_customer_360_05"):
    return get_client()[db_name]
