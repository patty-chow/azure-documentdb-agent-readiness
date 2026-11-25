import os
import asyncio
import random
import string
from typing import List
from .db import init_db, get_client
from .models import Profile
import numpy as np

try:
    import openai
except Exception:
    openai = None

EMBED_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DIM = 1536

def random_name():
    return "".join(random.choices(string.ascii_letters, k=8))

async def generate_embeddings(texts: List[str]):
    # If OpenAI key present, call embeddings; otherwise synthesize random normalized vectors
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key and openai:
        openai.api_key = api_key
        resp = openai.Embedding.create(model=EMBED_MODEL, input=texts)
        return [item['embedding'] for item in resp['data']]
    else:
        print("OPENAI_API_KEY not set or openai package unavailable; generating synthetic embeddings")
        vecs = [np.random.normal(size=(DIM,)).tolist() for _ in texts]
        # normalize
        vecs = [(v/np.linalg.norm(v)).tolist() for v in map(np.array, vecs)]
        return vecs

async def seed(n=100):
    # attempt to init beanie but continue if init fails due to driver differences
    try:
        await init_db()
    except Exception as e:
        print("init_db failed (continuing):", e)
    client = await get_client()
    db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_20")
    coll = client[db_name]["profiles"]

    # create synthetic profiles with some duplicates
    profiles = []
    texts = []
    for i in range(n):
        name = random_name()
        emails = [f"{name.lower()}@example.com"]
        if i % 20 == 0:
            # create a controlled duplicate
            emails.append(f"{name.lower()}.alt@example.com")
        text = name + " " + " ".join(emails)
        texts.append(text)
        profiles.append({"name": name, "emails": emails, "phones": [], "address": None, "source": {"source": "seed"}})

    embeddings = await generate_embeddings(texts)
    for p, e in zip(profiles, embeddings):
        p['embedding'] = e

    # insert many in batch
    await coll.delete_many({})
    await coll.insert_many(profiles)
    print(f"Inserted {n} profiles into {db_name}.profiles")

    # Create vector index using cosmosSearch via create_index
    index_spec = {
        "name": "profiles_embedding_hnsw",
        "cosmosSearchOptions": {
            "kind": "vector-hnsw",
            "dimensions": DIM,
            "similarity": "COS",
            "maxDegree": 32,
            "lBuild": 50
        }
    }
    try:
        # pymongo create_index with 'embedding' mapped to cosmosSearch
        await coll.create_index([("embedding", "cosmosSearch")], **index_spec)
        print("Created vector-hnsw index on profiles.embedding")
    except Exception as e:
        print("Index creation via driver failed:", e)
        print("Index may already exist or driver may not accept cosmosSearch via create_index.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--n', type=int, default=200)
    args = p.parse_args()
    asyncio.run(seed(args.n))