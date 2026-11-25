import os
import json
from flask import Flask, request, jsonify
from pymongo import MongoClient
from utils import bsonbinary_to_floats
import numpy as np

app = Flask(__name__)

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required")

client = MongoClient(DOCUMENTDB_URI)
db = client["sample_retail_01"]
col = db["products"]

# Helper: compute cosine similarity

def cosine_similarity(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def embed_text(text):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; cannot compute embeddings at query time.")
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        resp = openai.Embedding.create(model="text-embedding-ada-002", input=[text])
        return resp["data"][0]["embedding"]
    except Exception as e:
        raise RuntimeError(f"Embedding request failed: {e}")


@app.route("/search", methods=["POST"]) 
def search():
    body = request.get_json(force=True)
    q = body.get("q")
    if not q:
        return jsonify({"error": "missing 'q' in request body"}), 400

    try:
        q_emb = embed_text(q)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Fetch documents and compute similarity client-side by unpacking BSON Binary embeddings
    docs = list(col.find({}, {"title": 1, "description": 1, "price": 1, "category":1, "embedding":1}))
    results = []
    for d in docs:
        bin_emb = d.get("embedding")
        if not bin_emb:
            continue
        vec = bsonbinary_to_floats(bin_emb)
        score = cosine_similarity(q_emb, vec)
        results.append({"id": d.get("_id"), "title": d.get("title"), "description": d.get("description"), "price": d.get("price"), "category": d.get("category"), "score": score})

    results.sort(key=lambda r: r["score"], reverse=True)
    top10 = results[:10]
    return jsonify({"query": q, "results": top10})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
