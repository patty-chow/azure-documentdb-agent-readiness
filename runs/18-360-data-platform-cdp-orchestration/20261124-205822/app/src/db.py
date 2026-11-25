import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Read DOCUMENTDB_URI from env
MONGO_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_customer_360_18")

if not MONGO_URI:
    raise EnvironmentError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB")

# Singleton MongoClient as per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        # Rely on pymongo's defaults; the connection string (SRV) will enable TLS
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]
