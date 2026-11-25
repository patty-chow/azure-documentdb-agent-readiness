import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

DATABASE_NAME = "sample_healthcare_01"
COLLECTION_NAME = "patient_chunks"

def get_client():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise EnvironmentError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB cluster")
    try:
        client = MongoClient(uri)
        # quick sanity check
        _ = client.server_info()
        return client
    except ConfigurationError as e:
        raise

def get_db(client=None):
    if client is None:
        client = get_client()
    return client[DATABASE_NAME]

def get_collection(db=None):
    if db is None:
        db = get_db()
    return db[COLLECTION_NAME]
