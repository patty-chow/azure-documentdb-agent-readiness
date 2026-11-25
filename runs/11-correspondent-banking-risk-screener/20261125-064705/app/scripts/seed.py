"""Idempotent seed script: loads data/*.json into the sample_banking_11 database and computes embeddings for each document.

This script reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment. If OPENAI_API_KEY is missing,
it falls back to a deterministic synthetic embedding generator so the sample can be seeded without secrets.
"""
import json
import os
from pathlib import Path
import hashlib
import numpy as np

from src.db import get_collection, safe_create_indexes

TRY_USE_API = bool(os.environ.get("OPENAI_API_KEY"))

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def synthetic_embedding(text: str, dim: int = 1536):
    # deterministic embedding from SHA256; not a real semantic embedding but reproducible
    h = hashlib.sha256(text.encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
    v = rng.random(dim).astype(float)
    # normalize
    v = v / (np.linalg.norm(v) + 1e-12)
    return v.tolist()


def embed_texts_local(texts):
    if TRY_USE_API:
        # import lazily to avoid requiring openai at module import time
        from src.embeddings import embed_texts
        return embed_texts(texts)
    else:
        return [synthetic_embedding(t) for t in texts]


def ensure_and_seed():
    safe_create_indexes()

    # correspondents
    correspondents = load_json(DATA_DIR / "correspondents.json")
    coll = get_collection("correspondents")
    texts = [c.get("profile_text", "") for c in correspondents]
    embeddings = embed_texts_local(texts)
    for doc, emb in zip(correspondents, embeddings):
        doc["embedding"] = emb
        coll.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    print(f"Seeded {len(correspondents)} correspondents")

    # sanctions
    sanctions = load_json(DATA_DIR / "sanctions.json")
    coll = get_collection("sanctions")
    texts = [s.get("entry_text", "") for s in sanctions]
    embeddings = embed_texts_local(texts)
    for doc, emb in zip(sanctions, embeddings):
        doc["embedding"] = emb
        coll.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    print(f"Seeded {len(sanctions)} sanctions")

    # adverse media
    adverse = load_json(DATA_DIR / "adverse_media.json")
    coll = get_collection("adverse_media")
    texts = [a.get("snippet", "") for a in adverse]
    embeddings = embed_texts_local(texts)
    for doc, emb in zip(adverse, embeddings):
        doc["embedding"] = emb
        coll.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    print(f"Seeded {len(adverse)} adverse_media")


if __name__ == "__main__":
    ensure_and_seed()
