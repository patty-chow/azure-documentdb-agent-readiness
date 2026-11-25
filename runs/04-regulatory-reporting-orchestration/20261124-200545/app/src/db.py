import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

# Singleton MongoClient per documentdb-driver & documentdb-connection guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI is not set in the environment")
        # Use default pool settings appropriate for a small sample CLI app
        _client = MongoClient(uri, retryWrites=True)
        try:
            # Trigger a server selection to fail fast
            _client.admin.command('ping')
        except ConnectionFailure as e:
            raise RuntimeError(f"Could not connect to DocumentDB cluster: {e}")
    return _client


def get_db(db_name: str = None):
    client = get_client()
    if db_name is None:
        db_name = os.environ.get("DOCUMENTDB_DB", "sample_banking_04")
    return client[db_name]
