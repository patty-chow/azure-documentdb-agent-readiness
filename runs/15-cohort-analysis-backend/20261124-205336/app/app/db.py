from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = os.getenv("DB_NAME", "sample_customer_360_15")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable not set. Copy .env.example -> .env and set it.")

# Singleton MongoClient per process (documentdb-driver guidance)
_client = None

def get_client():
    global _client
    if _client is None:
        # Conservative defaults for a long-running server (OLTP)
        _client = MongoClient(
            DOCUMENTDB_URI,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            # socketTimeoutMS left default to allow longer-running aggregations
        )
        # Trigger immediate server selection to fail fast if misconfigured
        _client.admin.command('ping')
    return _client


def get_db():
    return get_client()[DB_NAME]
