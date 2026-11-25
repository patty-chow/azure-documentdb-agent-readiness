from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = os.environ.get("DB_NAME", "sample_healthcare_04")

# Singleton MongoClient per documentdb-driver guidance
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not MONGO_URI:
            raise RuntimeError("DOCUMENTDB_URI is not set in environment")
        _client = MongoClient(MONGO_URI)
    return _client


def get_collection(name: str):
    client = get_client()
    return client[DB_NAME][name]
