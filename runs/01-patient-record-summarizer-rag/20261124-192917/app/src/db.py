from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Singleton MongoClient per documentdb-driver guidance
_uri = os.environ.get("DOCUMENTDB_URI")
if not _uri:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required")

_client = MongoClient(_uri)
_db_name = "sample_healthcare_01"

def get_db():
    return _client[_db_name]

def get_client():
    return _client
