"""Script to load sample products, embed them, and insert into the products collection.

Usage:
  python scripts/load_data.py --file data/sample_products.json

It reads products, computes embeddings (using OPENAI_API_KEY if set), normalizes them, packs them as float32 bytes and inserts into the collection.

Be sure to set MONGO_URI and (optionally) OPENAI_API_KEY in your environment or .env.
"""
import os
import json
import argparse
import struct
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.binary import Binary
import numpy as np

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:10260/?tls=true")
DB_NAME = os.environ.get("DB_NAME", "product_catalog")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "products")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
    else:
        openai = None
except Exception:
    openai = None


def normalize(vec: np.ndarray) -> np.ndarray:
    v = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def pack_embedding(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def embed_text(text: str) -> np.ndarray:
    if openai is not None and OPENAI_API_KEY:
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
        vec = np.array(resp['data'][0]['embedding'], dtype=np.float32)
        return normalize(vec)
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    seed = int.from_bytes(h[:8], 'little')
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(EMBEDDING_DIMS).astype(np.float32)
    return normalize(vec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]

    with open(args.file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    docs = []
    for p in products:
        text = (p.get('title', '') or '') + '\n' + (p.get('description', '') or '')
        vec = embed_text(text)
        packed = pack_embedding(vec)
        doc = p.copy()
        doc['embedding'] = Binary(packed)
        doc['embeddingModel'] = EMBEDDING_MODEL
        doc['embeddingDims'] = EMBEDDING_DIMS
        docs.append(doc)

    if docs:
        coll.insert_many(docs)
        print(f"Inserted {len(docs)} documents into {DB_NAME}.{COLLECTION_NAME}")
    else:
        print("No documents to insert")

if __name__ == '__main__':
    main()
