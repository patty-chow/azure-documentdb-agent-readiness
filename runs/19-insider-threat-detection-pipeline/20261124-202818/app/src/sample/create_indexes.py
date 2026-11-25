"""Create a vector index on employee_vectors.embedding using the cosmosSearch pattern.

This script uses the MongoDB runCommand 'createIndexes' with cosmosSearchOptions as required by Azure DocumentDB.

Usage: python -m sample.create_indexes
"""
from sample.db import get_db
from sample.config import EMBEDDING_DIMS


def create_vector_index():
    db = get_db()
    coll_name = "employee_vectors"
    # ensure collection exists
    if coll_name not in db.list_collection_names():
        db.create_collection(coll_name)
    # build createIndexes command payload
    indexes = [
        {
            "key": {"embedding": "cosmosSearch"},
            "name": "embedding_vector_ivf",
            "cosmosSearchOptions": {
                "kind": "vector-ivf",
                "dimensions": EMBEDDING_DIMS,
                "similarity": "COS",
                "algorithmParameters": {"nlist": 1024}
            }
        }
    ]
    try:
        res = db.command({"createIndexes": coll_name, "indexes": indexes})
        print("createIndexes result:", res)
    except Exception as e:
        print("Error creating vector index:", e)


if __name__ == "__main__":
    create_vector_index()
