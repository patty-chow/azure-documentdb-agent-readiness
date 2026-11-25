from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise EnvironmentError("DOCUMENTDB_URI environment variable is required")
        # Use defaults; connection tuning can be adjusted per documentdb-connection guidance
        _client = MongoClient(uri)
    return _client


def get_db(name="sample_customer_360_12"):
    return get_client()[name]


def get_customers_collection():
    return get_db()["customers"]
