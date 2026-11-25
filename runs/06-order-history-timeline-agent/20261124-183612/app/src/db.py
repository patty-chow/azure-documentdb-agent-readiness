import os
from pymongo import MongoClient
from urllib.parse import quote_plus

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_mongo_client():
    global _client
    if _client is None:
        uri = os.environ.get('DOCUMENTDB_URI')
        if not uri:
            raise RuntimeError('DOCUMENTDB_URI is not set in the environment')
        # Use the raw URI provided
        _client = MongoClient(uri, tls=True)
    return _client


def get_db(db_name: str = None):
    db_name = db_name or os.environ.get('DOCUMENTDB_DB_NAME', 'sample_retail_06')
    client = get_mongo_client()
    return client[db_name]
