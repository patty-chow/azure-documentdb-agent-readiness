import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

# Database name per assumptions
DB_NAME = "sample_healthcare_19"

# Singleton client per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise ConfigurationError("DOCUMENTDB_URI environment variable is not set")
        # Use default options; documentdb cluster supports mongodb+srv or direct URI
        _client = MongoClient(uri)
    return _client


def get_db():
    return get_client()[DB_NAME]
