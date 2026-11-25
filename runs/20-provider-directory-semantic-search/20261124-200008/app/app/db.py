import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in environment or .env file")

# Driver best-practice: process-wide MongoClient singleton
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        # sensible pool/timeouts for sample app
        _client = MongoClient(
            DOCUMENTDB_URI,
            serverSelectionTimeoutMS=5000,
            maxIdleTimeMS=300000,
        )
    return _client


def get_db(name: str):
    return get_client()[name]
