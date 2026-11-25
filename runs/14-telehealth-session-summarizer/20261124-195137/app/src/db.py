import os
import time
from datetime import datetime
from pymongo import MongoClient

# Read connection details from env
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_healthcare_14")

# Singleton MongoClient per documentdb-driver and documentdb-connection guidance
_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        # Use reasonable defaults for a long-running app; tuned values are application-specific.
        _client = MongoClient(DOCUMENTDB_URI,
                              retryWrites=True,
                              serverSelectionTimeoutMS=5000,
                              socketTimeoutMS=300000,
                              maxPoolSize=20)
    return _client


def get_db():
    client = get_client()
    return client[DATABASE_NAME]


def get_collections():
    db = get_db()
    return {
        "clinical_summaries": db["clinical_summaries"],
        "patients": db["patients"],
        "transcripts": db["transcripts"],
    }


def create_indexes():
    cols = get_collections()
    # patientId index for lookups
    cols["clinical_summaries"].create_index([("patientId", 1)], name="idx_patientId")
    # Consider TTL or vector indexes separately; omitted by default to avoid cluster changes.


if __name__ == "__main__":
    print("Creating indexes...")
    create_indexes()
    print("Done", datetime.utcnow().isoformat())
