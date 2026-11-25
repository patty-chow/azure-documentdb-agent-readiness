import os
from pymongo import MongoClient
from dotenv import load_dotenv
import hashlib
import struct

load_dotenv()

DB_NAME = "sample_customer_360_10"
COLLECTION = "kb_documents"

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI not set in environment")

# Connection: follow singleton pattern
_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def pseudo_embedding(text, dim=1536):
    # Deterministic pseudo-embedding for demos without an embedding provider
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand to dim floats in [-1,1]
    vals = []
    while len(vals) < dim:
        for i in range(0, len(h), 4):
            if len(vals) >= dim:
                break
            chunk = h[i:i+4]
            v = struct.unpack("!I", chunk)[0]
            vals.append(((v % 1000) / 1000.0) * 2 - 1)
        h = hashlib.sha256(h).digest()
    return vals[:dim]


def search_similar(embedding, k=5):
    """Run a vector k-NN search using the $search aggregation stage against the
    embedding field. Returns list of docs with score.
    """
    client = get_client()
    db = client[DB_NAME]
    col = db[COLLECTION]

    lSearch = max(k, 40)
    pipeline = [
        {"$search": {"cosmosSearch": {"path": "embedding", "vector": embedding, "k": k, "lSearch": lSearch}}},
        {"$project": {"title": 1, "content": 1, "metadata": 1, "score": {"$meta": "searchScore"}}},
    ]

    results = list(col.aggregate(pipeline))
    return results


def get_top_k_for_text(text, embedder=None, k=5):
    if embedder is not None:
        emb = embedder(text)
    else:
        emb = pseudo_embedding(text)
    return search_similar(emb, k=k)
