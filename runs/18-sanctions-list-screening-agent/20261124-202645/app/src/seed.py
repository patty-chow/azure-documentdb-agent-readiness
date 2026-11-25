import os
import time
import random
from typing import List

from src.db import get_sanctions_collection

try:
    import openai
except Exception:
    openai = None


EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def make_synthetic_entry(i: int):
    name = f"Person {i}"
    alt_names = [f"P. {i}", f"Person_{i}"]
    country = random.choice(["US", "GB", "CA", "AU", "FR", "DE"]) 
    details = f"Synthetic sanctions entry #{i}"
    return {
        "_id": f"sanction_{i}",
        "name": name,
        "alt_names": alt_names,
        "country": country,
        "details": details,
        # embedding will be added later
    }


def compute_embedding(text: str) -> List[float]:
    if openai is None:
        raise RuntimeError("openai package not available")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — cannot compute embeddings")
    openai.api_key = api_key
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    return resp["data"][0]["embedding"]


def seed(n: int = 200):
    coll = get_sanctions_collection()
    docs = [make_synthetic_entry(i) for i in range(1, n + 1)]

    # compute embeddings if possible
    can_embed = os.environ.get("OPENAI_API_KEY") and openai is not None
    for d in docs:
        if can_embed:
            text = d["name"] + " " + " ".join(d.get("alt_names", [])) + " " + d["details"]
            try:
                emb = compute_embedding(text)
                d["embedding"] = emb
            except Exception as e:
                print("Warning: embedding generation failed:", e)
                d["embedding"] = []
        else:
            d["embedding"] = []

    # upsert documents idempotently
    for d in docs:
        coll.replace_one({"_id": d["_id"]}, d, upsert=True)
    print(f"Seeded {len(docs)} documents into {coll.full_name}")


if __name__ == "__main__":
    n = int(os.environ.get("SEED_COUNT", "200"))
    seed(n)
