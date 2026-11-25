import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_healthcare_02")

_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise ConfigurationError("DOCUMENTDB_URI is not set in the environment")
        # Use a singleton MongoClient per driver guidance
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]
