import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DOCUMENT_DB = os.environ.get("DOCUMENTDB_URI")
DB_NAME = "sample_banking_11"

if not DOCUMENT_DB:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to run this sample")

client = MongoClient(DOCUMENT_DB)
db = client[DB_NAME]


def get_collection(name: str):
    return db[name]


def safe_create_indexes():
    """Try to create simple indexes. Server-side vector index creation is intentionally conservative here: the sample
    computes similarity client-side. If the server supports a managed vector index the user can add it manually.
    """
    try:
        # Create simple indexes for identify lookups
        db.correspondents.create_index([("_id", 1)], name="pk_correspondents")
        db.sanctions.create_index([("_id", 1)], name="pk_sanctions")
        db.adverse_media.create_index([("_id", 1)], name="pk_adverse_media")
    except PyMongoError as e:
        print("Warning: could not create basic indexes:", e)


def list_collections():
    return db.list_collection_names()
