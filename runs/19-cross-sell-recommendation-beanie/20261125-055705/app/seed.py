"""
Idempotent seeding script: creates sample products, orders, product_pairs and computes embeddings via OpenAI.
If OPENAI_API_KEY is not set, the script will generate random normalized placeholder embeddings so the database can be populated for local verification.
Run: python seed.py
"""
import os
import asyncio
import random
import itertools
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import Product, ProductPair, Order
import openai
import numpy as np

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_retail_19")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

SAMPLE_PRODUCT_COUNT = int(os.environ.get("SAMPLE_PRODUCT_COUNT", 50))
SAMPLE_ORDER_COUNT = int(os.environ.get("SAMPLE_ORDER_COUNT", 500))
MAX_ITEMS_PER_ORDER = int(os.environ.get("MAX_ITEMS_PER_ORDER", 6))
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSIONS", 1536))

async def compute_embedding(text: str):
    # If OpenAI key is present, ask OpenAI; otherwise create a random normalized placeholder vector.
    if OPENAI_API_KEY:
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
        vec = resp["data"][0]["embedding"]
        a = np.array(vec, dtype=float)
        norm = np.linalg.norm(a)
        if norm == 0:
            return vec
        return (a / norm).tolist()
    else:
        # Dev-only placeholder embedding
        a = np.random.RandomState(abs(hash(text)) % (2**32)).randn(EMBEDDING_DIM)
        a = a.astype(float)
        n = np.linalg.norm(a)
        if n == 0:
            return a.tolist()
        return (a / n).tolist()

async def main():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    await init_beanie(database=client[DATABASE_NAME], document_models=[Product, ProductPair, Order])

    # Create products
    products = []
    for i in range(1, SAMPLE_PRODUCT_COUNT + 1):
        pid = f"prod_{i}"
        name = f"Product {i}"
        emb = await compute_embedding(name)
        p = Product(id=pid, name=name, embedding=emb, embedding_model=EMBEDDING_MODEL, dimensions=len(emb))
        await p.save()
        products.append(pid)

    # Create random orders
    for i in range(SAMPLE_ORDER_COUNT):
        k = random.randint(1, MAX_ITEMS_PER_ORDER)
        items = random.sample(products, k)
        oid = f"order_{i}_{random.randint(1,1000000)}"
        o = Order(id=oid, items=items, ts=datetime.utcnow())
        await o.insert()

    # Aggregate co-purchase pairs and upsert into product_pairs
    pair_counts = {}
    # Use raw Motor cursor to tolerate existing ObjectId ids in the collection
    raw_cursor = client[DATABASE_NAME]["orders"].find({})
    async for order_doc in raw_cursor:
        items = order_doc.get("items", [])
        items = sorted(items)
        for a, b in itertools.combinations(items, 2):
            key = (a, b)
            pair_counts[key] = pair_counts.get(key, 0) + 1

    for (a, b), count in pair_counts.items():
        pid = f"{a}__{b}"
        combined_text = f"{a} {b}"
        emb = await compute_embedding(combined_text)
        pp = ProductPair(id=pid, product_ids=[a, b], count=count, embedding=emb, embedding_model=EMBEDDING_MODEL, dimensions=len(emb), updated_at=datetime.utcnow())
        await pp.save()

    print("Seeding complete")

if __name__ == '__main__':
    asyncio.run(main())
