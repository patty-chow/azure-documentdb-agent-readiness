import os
import threading
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

load_dotenv()

# Read DOCUMENTDB_URI from environment
_DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not _DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is not set. See .env.example")

# Singleton MongoClient per process (driver best practice)
_client = None
_client_lock = threading.Lock()

def get_client() -> MongoClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                # Let the URI provide TLS and options. We rely on pymongo defaults for pool sizing.
                _client = MongoClient(_DOCUMENTDB_URI)
                # Optionally, could call _client.admin.command('ping') here to validate connectivity.
    return _client


def get_db():
    """Return the sample database object."""
    client = get_client()
    return client["sample_customer_360_08"]
