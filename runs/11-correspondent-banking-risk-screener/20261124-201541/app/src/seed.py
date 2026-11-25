import json
import os
from pathlib import Path
from src.db import get_db, create_collections_and_indexes
from dotenv import load_dotenv

load_dotenv()

SEED_DIR = Path(__file__).parent.parent / "seed"


def load_json_to_collection(filename, collection_name):
    db = get_db()
    with open(filename, "r", encoding="utf-8") as f:
        docs = json.load(f)
    if docs:
        coll = db[collection_name]
        # Upsert by _id
        for d in docs:
            coll.replace_one({"_id": d["_id"]}, d, upsert=True)
    print(f"Loaded {filename} -> {collection_name}")


def seed_all():
    create_collections_and_indexes()
    load_json_to_collection(SEED_DIR / "correspondents.json", "correspondents")
    load_json_to_collection(SEED_DIR / "sanctions.json", "sanctions")
    load_json_to_collection(SEED_DIR / "adverse_media.json", "adverse_media")


if __name__ == "__main__":
    seed_all()
    print("Seeding complete.")
