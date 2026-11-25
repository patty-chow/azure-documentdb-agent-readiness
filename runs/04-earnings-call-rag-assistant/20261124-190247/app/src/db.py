import os
from pymongo import MongoClient

# Read connection string from env var
URI = os.getenv("DOCUMENTDB_URI")
if not URI:
    raise EnvironmentError("DOCUMENTDB_URI is not set in the environment. See .env.example")

# Singleton client
_client = None

def get_client():
    global _client
    if _client is None:
        # Let the user supply the full connection string including credentials
        _client = MongoClient(URI)
    return _client


def get_db(db_name="sample_fintech_04"):
    return get_client()[db_name]
