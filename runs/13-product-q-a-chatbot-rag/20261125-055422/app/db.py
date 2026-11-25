from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get('DOCUMENTDB_URI')
DB_NAME = os.environ.get('DB_NAME', 'sample_retail_13')

_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError('DOCUMENTDB_URI environment variable is not set')
        # Singleton MongoClient per documentdb-driver guidance
        _client = MongoClient(DOCUMENTDB_URI, retryWrites=True, retryReads=True, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    return get_client()[DB_NAME]
