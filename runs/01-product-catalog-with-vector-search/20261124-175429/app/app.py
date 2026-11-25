import os
import struct
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.binary import Binary
import numpy as np

load_dotenv()

# Configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:10260/?tls=true")
DB_NAME = os.environ.get("DB_NAME", "product_catalog")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "products")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Singleton MongoClient per documentdb-driver guidance
_client = None

def get_client():
    global _client
    if _client is None:
        # Follow documentdb-connection guidance: use SRV/TLS if provided in MONGO_URI
        _client = MongoClient(MONGO_URI)
    return _client


def normalize(vec: np.ndarray) -> np.ndarray:
    v = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def pack_embedding(vec: np.ndarray) -> bytes:
    # pack as little-endian float32
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def unpack_embedding(b: bytes) -> list:
    count = len(b) // 4
    return list(struct.unpack(f"{count}f", b))


# Embedding provider: real OpenAI when key present, fallback deterministic hash-based mock
try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
    else:
        openai = None
except Exception:
    openai = None


def embed_text(text: str) -> np.ndarray:
    """Return a numpy array of length EMBEDDING_DIMS.
    If OPENAI_API_KEY is set and openai is available, call the API.
    Otherwise return a deterministic mock embedding (not semantically meaningful) for offline dev.
    """
    if openai is not None and OPENAI_API_KEY:
        # Real embedding call
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
        vec = np.array(resp['data'][0]['embedding'], dtype=np.float32)
        return normalize(vec)
    # Fallback deterministic mock: hash the text into a seed and generate pseudo-random vector
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    seed = int.from_bytes(h[:8], 'little')
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(EMBEDDING_DIMS).astype(np.float32)
    return normalize(vec)


app = Flask(__name__)


@app.route('/search', methods=['POST'])
def search():
    payload = request.json or {}
    query = payload.get('q') or payload.get('query')
    k = int(payload.get('k', 10))
    if not query:
        return jsonify({"error": "query parameter 'q' required in JSON body"}), 400

    qvec = embed_text(query)
    # Pack to BSON binary in same format as stored to allow server-side vector search if supported
    qbin = Binary(pack_embedding(qvec))

    # Build a $search aggregation stage using cosmosSearch / vector query
    # The exact server-side syntax may vary; this sample shows the intended pattern.
    # For providers that expose 'cosmosSearch' vector knn, it will look similar to below.
    k = min(k, 50)
    db = get_client()[DB_NAME]
    coll = db[COLLECTION_NAME]

    # If the server supports $search with cosmosSearch, you could run an aggregation like this.
    # We attempt it; if it fails because the cluster doesn't support it, fall back to in-memory distance ranking.
    try:
        pipeline = [
            {
                "$search": {
                    "knn": {
                        "vector": {"path": "embedding", "queryVector": qbin},
                        "k": k,
                        "similarity": "COS"  # or L2/IP depending on index
                    }
                }
            },
            {"$limit": k},
            {"$project": {"title": 1, "description": 1, "price": 1, "score": {"$meta": "searchScore"}}}
        ]
        docs = list(coll.aggregate(pipeline))
        # Convert any Binary embedding fields to lengths or omit embedding in response
        for d in docs:
            d.pop('embedding', None)
        return jsonify({'results': docs})
    except Exception as e:
        # Fallback: fetch all documents, compute cosine similarity in-app
        all_docs = list(coll.find({}, {'title': 1, 'description': 1, 'price': 1, 'embedding': 1}))
        results = []
        for d in all_docs:
            emb_b = d.get('embedding')
            if emb_b:
                try:
                    vec = np.array(unpack_embedding(emb_b), dtype=np.float32)
                    # normalize just in case
                    vec = normalize(vec)
                    score = float(np.dot(qvec, vec))
                except Exception:
                    score = 0.0
            else:
                score = 0.0
            results.append((score, d))
        results.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, d in results[:k]:
            d.pop('embedding', None)
            d['score'] = score
            out.append(d)
        return jsonify({'results': out})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
