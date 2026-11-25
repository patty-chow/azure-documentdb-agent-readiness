import os
import json
import argparse
import random
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    print("DOCUMENTDB_URI not set. Set it in .env before running the seed script.")
    raise SystemExit(1)

from pymongo import MongoClient

EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))

SAMPLE_PATH = Path(__file__).parent.parent / "sample_data" / "products.json"


def generate_random_embedding(dims):
    v = np.random.normal(size=(dims,)).astype(float)
    v = v / np.linalg.norm(v)
    return v.tolist()


def load_products():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main(use_openai: bool = False, skip_embed: bool = False):
    client = MongoClient(DOCUMENTDB_URI, retryWrites=False)
    db = client["sample_retail_04"]
    col = db["products"]
    products = load_products()
    to_insert = []
    for p in products:
        doc = {
            "product_id": p["product_id"],
            "title": p["title"],
            "description": p["description"],
            "metadata": p.get("metadata", {}),
            "schemaVersion": "1",
        }
        if skip_embed:
            doc["embedding"] = generate_random_embedding(EMBEDDING_DIMS)
        else:
            # seed with random embeddings by default; calling real embedding provider is optional
            doc["embedding"] = generate_random_embedding(EMBEDDING_DIMS)
        to_insert.append(doc)
    # upsert by product_id
    for d in to_insert:
        col.update_one({"product_id": d["product_id"]}, {"$set": d}, upsert=True)
    print(f"Upserted {len(to_insert)} products into sample_retail_04.products")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-embed", action="store_true", help="Insert random embeddings instead of calling OpenAI")
    args = parser.parse_args()
    main(skip_embed=args.skip_embed)
