from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Read the connection string at runtime from environment variable
MONGO_URI = os.environ.get("DOCUMENTDB_URI")
if not MONGO_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB")

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    client = get_client()
    return client['sample_banking_05']
