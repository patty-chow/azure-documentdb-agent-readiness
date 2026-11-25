"""Ingestion script to generate synthetic products and insert them into the sample DocumentDB.

Usage:
    python scripts/ingest.py --count 10000

The script will:
- Connect to the DOCUMENTDB_URI database from environment
- Ensure a vector index exists (script attempts to create an index via a best-effort pymongo runCommand)
- Generate synthetic products using Faker
- Generate embeddings via OpenAI if OPENAI_API_KEY is set, otherwise use deterministic random vectors
- Insert documents in batches for performance

Note: This script is safe to run repeatedly; product_id values are deterministic per run seed so
re-running with the same seed will create duplicates unless the collection is cleared.
"""

import asyncio
import argparse
import random
import os
from typing import List

from faker import Faker
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings
from app.models import Product

try:
    import openai
except Exception:
    openai = None


# Constants matching our embedding model choice
EMBEDDING_DIMS = 1536
DEFAULT_BATCH = 200


async def ensure_index(client: AsyncIOMotorClient):
    """Attempt to create a vector HNSW index on the 'embedding' field.

    This function uses the low-level createIndexes runCommand JSON shape which some
    DocumentDB clusters expect for vector index creation. It is best-effort: if the
    server does not support the shape or returns an error, the function logs and continues.
    """
    db = client[settings.DB_NAME]
    try:
        # The exact index creation document shape for DocumentDB vector indexes can vary by version.
        # We attempt a createIndexes command that includes cosmosSearchOptions with vector-hnsw.
        cmd = {
            "createIndexes": "products",
            "indexes": [
                {
                    "key": {"embedding": "vector"},
                    "name": "embedding_vector_hnsw",
                    "cosmosSearchOptions": {
                        "kind": "vector-hnsw",
                        "dimensions": EMBEDDING_DIMS,
                        "m": 16,
                        "efConstruction": 200,
                    },
                }
            ],
        }
        # run the command (some servers may accept; others may reject - fail silently)
        res = await db.command(cmd)
        print("Index creation command result:", res)
    except Exception as e:
        print("Warning: index creation via runCommand failed or is unsupported in this environment:", e)
        print("The cluster may already have the index or you can create it via the MCP tool or portal.")


def deterministic_vector(seed: int, dims: int = EMBEDDING_DIMS) -> List[float]:
    """Return a deterministic pseudorandom vector for local runs when no embedding API is available."""
    rnd = random.Random(seed)
    return [rnd.uniform(-1, 1) for _ in range(dims)]


async def generate_and_insert(count: int = 10000):
    """Generate `count` synthetic products, compute embeddings, and insert into the products collection.

    The function batches inserts for performance and writes simple product documents compatible
    with the Product Beanie model.
    """
    fake = Faker()
    client = AsyncIOMotorClient(settings.DOCUMENTDB_URI)

    # Ensure index exists (best-effort)
    await ensure_index(client)

    await init_beanie(database=client[settings.DB_NAME], document_models=[Product])

    batch = []
    for i in range(count):
        product_id = f"SKU-{i:06d}"
        name = fake.catch_phrase()
        description = fake.text(max_nb_chars=200)
        category = fake.word()
        price = round(random.uniform(5, 500), 2)
        attributes = {"color": fake.color_name(), "brand": fake.company()}

        # Embedding: try OpenAI if available, otherwise deterministic random vector
        if settings.OPENAI_API_KEY and openai is not None:
            try:
                # Use OpenAI embeddings API synchronously for simplicity
                openai.api_key = settings.OPENAI_API_KEY
                emb_resp = openai.Embedding.create(input=f"{name}. {description}", model="text-embedding-3-small")
                vector = emb_resp["data"][0]["embedding"]
            except Exception as e:
                print("OpenAI embedding failed, falling back to deterministic vector:", e)
                vector = deterministic_vector(i)
        else:
            vector = deterministic_vector(i)

        doc = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "price": price,
            "attributes": attributes,
            "embedding": vector,
        }
        batch.append(doc)

        if len(batch) >= DEFAULT_BATCH:
            await client[settings.DB_NAME]["products"].insert_many(batch)
            print(f"Inserted {i+1} / {count}")
            batch = []

    if batch:
        await client[settings.DB_NAME]["products"].insert_many(batch)
        print(f"Inserted final batch, total {count}")

    print("Ingestion complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=int(os.environ.get("INGEST_COUNT", 10000)))
    args = parser.parse_args()

    print(f"Starting ingestion of {args.count} products into database {settings.DB_NAME}")
    asyncio.run(generate_and_insert(args.count))


if __name__ == "__main__":
    main()
