import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Read connection details from environment
MONGO_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = os.environ.get("DATABASE_NAME", "sample_healthcare_10")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "formulary")

if not MONGO_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB.")

# Singleton client per process (documentdb-driver best practice)
_client = None
_client_connect_promise = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
        # connect lazily; operations will trigger connection
    return _client

def get_collection():
    client = get_client()
    db = client[DB_NAME]
    return db[COLLECTION_NAME]
