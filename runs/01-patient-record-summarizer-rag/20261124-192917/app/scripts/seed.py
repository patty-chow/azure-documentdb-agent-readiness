"""Seed the sample 'patient_chunks' collection with synthetic data.

- Idempotent: drops and recreates the collection contents for the 'sample_healthcare_01' database.
- Generates embeddings using OpenAI (if OPENAI_API_KEY present) else deterministic random vectors.
"""
import os
import random
import uuid
import json
import sys
from datetime import datetime
from pathlib import Path
# ensure src is importable when running from scripts/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.db import get_db
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))

try:
    import openai
    openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None

COLLECTION = "patient_chunks"

NUM_PATIENTS = 10
CHUNKS_PER_PATIENT = 6

# deterministic RNG for synthetic embeddings if OpenAI key missing
RNG_SEED = 42


def make_text(patient_idx, chunk_idx):
    return f"Patient {patient_idx} record chunk {chunk_idx}: vitals normal. note: synthetic example for testing. chunk_id={chunk_idx}"


def gen_synthetic_embedding(text, dims=EMBEDDING_DIMS):
    # deterministic pseudo-random vector from hash of text
    rnd = random.Random(RNG_SEED + abs(hash(text)) % 100000)
    v = [rnd.random() - 0.5 for _ in range(dims)]
    # normalize
    norm = sum(x*x for x in v) ** 0.5
    if norm == 0:
        return [0.0]*dims
    return [x / norm for x in v]


def embed_texts(texts):
    if openai and OPENAI_API_KEY:
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=texts)
        return [item['embedding'] for item in resp['data']]
    else:
        return [gen_synthetic_embedding(t) for t in texts]


def seed():
    db = get_db()
    coll = db[COLLECTION]
    # Idempotent: remove existing docs for sample patients
    coll.delete_many({})

    docs = []
    for p in range(1, NUM_PATIENTS + 1):
        patientId = f"patient_{p:03d}"
        for c in range(1, CHUNKS_PER_PATIENT + 1):
            text = make_text(p, c)
            docs.append({
                "patientId": patientId,
                "sourceDocId": f"doc_{p:03d}",
                "chunkId": c,
                "text": text,
                "schemaVersion": 1,
                "createdAt": datetime.utcnow()
            })

    # create embeddings in batches
    texts = [d['text'] for d in docs]
    embeddings = embed_texts(texts)
    for d, e in zip(docs, embeddings):
        d['embedding'] = e

    # insert
    res = coll.insert_many(docs)
    print(f"Inserted {len(res.inserted_ids)} documents into {COLLECTION}")


if __name__ == '__main__':
    seed()
