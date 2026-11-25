"""Create a DocumentDB vector index for the products collection.

This script attempts to call the server-side createSearchIndexes command. The exact command
shape may vary by DocumentDB version; if the command fails, it prints the payload you can use
with mongosh or the portal.

By default this creates a vector-ivf index with COS similarity and IVF-specific options.
"""
import os
import json
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:10260/?tls=true")
DB_NAME = os.environ.get("DB_NAME", "product_catalog")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "products")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

index_payload = {
    "createSearchIndexes": COLLECTION_NAME,
    "indexes": [
        {
            "name": "embedding_vector_ivf",
            "key": {"embedding": "cosmosSearch"},
            "cosmosSearchOptions": {
                "kind": "vector-ivf",
                "dimensions": EMBEDDING_DIMS,
                "similarity": "COS",
                "options": {"nlist": 100}
            }
        }
    ]
}

print("Index payload:\n", json.dumps(index_payload, indent=2))

try:
    resp = db.command(index_payload)
    print("createSearchIndexes response:", resp)
except Exception as e:
    print("Failed to create index via db.command (this may require the DocumentDB gateway or cloud cluster).\nError:", e)
    print("Use the above payload with mongosh or the portal's createSearchIndexes administrative API.")
