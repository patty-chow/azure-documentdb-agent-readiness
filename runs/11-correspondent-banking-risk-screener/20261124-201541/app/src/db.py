import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = os.environ.get("DB_NAME", "sample_banking_11")

_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable is required")
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    return get_client()[DB_NAME]


def create_collections_and_indexes():
    db = get_db()
    # Create collections if they do not exist
    for coll in ("correspondents", "sanctions", "adverse_media"):
        if coll not in db.list_collection_names():
            db.create_collection(coll)

    # Create a vector index on the 'embedding' field for the collections used in vector search
    try:
        for coll in ("correspondents", "sanctions", "adverse_media"):
            idx = {
                "name": f"embedding_vector_idx_{coll}",
                "key": {"cosmosSearch": "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": "vector-hnsw",
                    "path": "embedding",
                    "dimensions": int(os.environ.get("EMBEDDING_DIMS", 1536)),
                    "similarity": "COS"
                }
            }
            cmd = {"createIndexes": coll, "indexes": [idx]}
            db.command(cmd)
    except Exception as e:
        # Index creation may fail if it already exists or server rejects it
        print("Warning: vector index creation may have failed:", e)

    # Create a simple full-text search index (if supported) for sanctions and adverse_media
    try:
        search_idx = {
            "name": "text_search_idx",
            "definition": {
                "mappings": {
                    "dynamic": True
                }
            }
        }
        # use database command createSearchIndexes if available
        db.command({"createSearchIndexes": "sanctions", "indexes": [search_idx]})
        db.command({"createSearchIndexes": "adverse_media", "indexes": [search_idx]})
    except Exception as e:
        print("Note: createSearchIndexes command may not be available or may have failed:", e)


if __name__ == "__main__":
    print("Creating collections and indexes in DB:", DB_NAME)
    create_collections_and_indexes()
    print("Done.")
