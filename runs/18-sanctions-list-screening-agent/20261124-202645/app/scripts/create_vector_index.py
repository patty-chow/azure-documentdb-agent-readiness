"""One-shot script to create a cosmosSearch vector-hnsw index on sample_banking_18.sanctions"""
import os
from pymongo import MongoClient

uri = os.environ.get("DOCUMENTDB_URI")
if not uri:
    raise SystemExit("DOCUMENTDB_URI not set")

client = MongoClient(uri)
db = client["sample_banking_18"]

cmd = {
    "createIndexes": "sanctions",
    "indexes": [
        {
            "name": "embedding_vector_idx",
            "key": {"embedding": "cosmosSearch"},
            "cosmosSearchOptions": {
                "kind": "vector-hnsw",
                "dimensions": 1536,
                "similarity": "COS",
                "m": 16,
                "efConstruction": 64
            }
        }
    ]
}

res = db.command(cmd)
print("createIndexes result:", res)
