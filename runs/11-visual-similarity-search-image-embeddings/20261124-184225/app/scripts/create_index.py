"""Create a cosmosSearch vector index on sample_retail_11.products using PyMongo createIndexes command."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise SystemExit("DOCUMENTDB_URI not set")

client = MongoClient(DOCUMENTDB_URI, tls=True)
db = client["sample_retail_11"]

cmd = {
    "createIndexes": "products",
    "indexes": [
        {
            "key": {"embedding": "cosmosSearch"},
            "name": "products_embedding_ivf",
            "cosmosSearchOptions": {
                "kind": "vector-ivf",
                "dimensions": 512,
                "similarity": "COS",
                "numLists": 100
            }
        }
    ]
}

res = db.command(cmd)
print("createIndexes result:", res)
