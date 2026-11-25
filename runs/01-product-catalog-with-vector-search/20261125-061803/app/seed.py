import os
import json
import sys
from pymongo import MongoClient
from bson import Binary
from utils import floats_to_bsonbinary

DB_NAME = "sample_retail_01"
COLLECTION = "products"

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not DOCUMENTDB_URI:
    print("ERROR: DOCUMENTDB_URI environment variable is required.")
    sys.exit(1)

client = MongoClient(DOCUMENTDB_URI)
db = client[DB_NAME]
col = db[COLLECTION]

# Load sample products
here = os.path.dirname(__file__)
with open(os.path.join(here, "data/sample_products.json"), "r", encoding="utf-8") as f:
    products = json.load(f)

# Load embeddings: prefer to compute with OpenAI if key present; otherwise use precomputed file
embeddings = {}
if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        texts = [p["title"] + " - " + p.get("description", "") for p in products]
        print("Requesting embeddings from OpenAI...")
        resp = openai.Embedding.create(model="text-embedding-ada-002", input=texts)
        for p, r in zip(products, resp["data"]):
            embeddings[str(p["_id"])] = r["embedding"]
    except Exception as e:
        print("OpenAI embedding call failed:", e)
        print("Falling back to data/sample_embeddings.json if present.")

if not embeddings:
    with open(os.path.join(here, "data/sample_embeddings.json"), "r", encoding="utf-8") as f:
        embeddings = json.load(f)

# Prepare documents with BSON Binary embeddings
docs = []
for p in products:
    emb = embeddings.get(str(p["_id"]))
    if not emb:
        print(f"Missing embedding for id {p['_id']}, skipping")
        continue
    doc = p.copy()
    doc["embedding"] = floats_to_bsonbinary(emb)
    docs.append(doc)

# Insert docs (drop existing collection for idempotence)
print(f"Dropping collection {DB_NAME}.{COLLECTION} if it exists...")
col.drop()

if docs:
    print(f"Inserting {len(docs)} documents...")
    col.insert_many(docs)
else:
    print("No documents to insert.")

# Attempt to create a server-side vector index (plausible MongoDB 7+ style). If it fails, show error and continue.
dims = len(next(iter(embeddings.values())))
index_name = "embedding_vector_knn"
try:
    print("Attempting to create a server-side IVF knn vector index...")
    # This createIndexes command is a plausible shape for MongoDB 7 vector search; target cluster may accept it.
    cmd = {
        "createIndexes": COLLECTION,
        "indexes": [
            {
                "key": {"embedding": "knnVector"},
                "name": index_name,
                "knnVector": {
                    "dimensions": dims,
                    "method": "ivf",
                    "type": "float32",
                    "parameters": {"nlist": 100}
                }
            }
        ]
    }
    res = db.command(cmd)
    print("Index creation response:", res)
except Exception as e:
    print("Server-side index creation failed (this may be expected on some clusters):", e)
    print("You can still perform client-side ranking; check cluster docs for exact createIndexes syntax supported by your server.")

print("Seeding complete.")
