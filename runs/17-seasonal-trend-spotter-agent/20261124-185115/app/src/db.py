import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI is not set in the environment")
        # Use defaults; caller can tune pool sizes if needed
        _client = MongoClient(uri)
    return _client


def get_db(name="sample_retail_17"):
    return get_client()[name]
