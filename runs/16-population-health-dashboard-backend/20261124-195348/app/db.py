import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not _DOCUMENTDB_URI:
            raise ConfigurationError("DOCUMENTDB_URI is not set in the environment")
        # Use the SRV-style connection string provided by the environment
        _client = MongoClient(_DOCUMENTDB_URI, tls=True)
    return _client


def get_db(name: str = "sample_healthcare_16"):
    client = get_client()
    return client[name]
