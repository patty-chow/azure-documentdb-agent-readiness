import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

# singleton client per process (documentdb-driver guidance)
_DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
_DB_NAME = os.environ.get("DB_NAME", "sample_banking_17")

if not _DOCUMENTDB_URI:
    raise ConfigurationError("DOCUMENTDB_URI environment variable is not set. Copy .env.example to .env and set it.")

# Basic client options — keep defaults reasonable; app is a CLI/long-running sample
_client = MongoClient(_DOCUMENTDB_URI, retryWrites=True)

def get_client():
    """Return the singleton MongoClient."""
    return _client

def get_db():
    return _client[_DB_NAME]
