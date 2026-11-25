#!/usr/bin/env python3
"""Seed script: idempotently upserts sample reviews into sample_retail_07.reviews
If data/sample_reviews.json is empty, this script generates 100 synthetic reviews.
"""
import os
import json
import asyncio
import sys
from datetime import datetime, timedelta
from random import choice, randint, seed
from pathlib import Path

# ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sample_retail_07.db import init_db
from src.sample_retail_07.models import Review

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_reviews.json")

SAMPLE_TEXTS = {
    "positive": [
        "Great product, exceeded my expectations",
        "High quality and fast shipping. Very happy!",
        "Five stars. Would buy again",
        "Excellent value for money",
        "Works as described, no complaints"
    ],
    "negative": [
        "Terrible experience, broke after a week",
        "Poor quality and slow shipping",
        "Not as described, disappointed",
        "Would not recommend",
        "Very unhappy with this purchase"
    ],
    "mixed": [
        "Good quality but overpriced",
        "Decent product but shipping took too long",
        "Works well but packaging was damaged",
        "Nice features but some reliability concerns",
        "OK for the price, could be better"
    ]
}

async def load_or_generate_data():
    path = os.path.abspath(DATA_FILE)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump([], f)
    with open(path, "r+") as f:
        try:
            data = json.load(f)
        except Exception:
            data = []
        if not data:
            seed(1)
            products = [f"P{n}" for n in range(1, 11)]
            users = [f"U{n}" for n in range(1, 51)]
            now = datetime.utcnow()
            for i in range(100):
                tone = choice(["positive","negative","mixed"])
                text = choice(SAMPLE_TEXTS[tone])
                rec = {
                    "review_id": f"R{i+1}",
                    "product_id": choice(products),
                    "user_id": choice(users),
                    "review_text": text,
                    "created_at": (now - timedelta(days=randint(0, 365))).isoformat(),
                }
                data.append(rec)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    return data

async def seed_db():
    data = await load_or_generate_data()
    await init_db()
    for rec in data:
        try:
            created_at = datetime.fromisoformat(rec.get("created_at"))
        except Exception:
            created_at = datetime.utcnow()
        existing = await Review.find_one(Review.review_id == rec["review_id"])
        if existing:
            # update fields that may have changed
            existing.product_id = rec["product_id"]
            existing.user_id = rec["user_id"]
            existing.review_text = rec["review_text"]
            existing.created_at = created_at
            await existing.save()
        else:
            doc = Review(
                review_id=rec["review_id"],
                product_id=rec["product_id"],
                user_id=rec["user_id"],
                review_text=rec["review_text"],
                created_at=created_at,
            )
            await doc.insert()
    print(f"Seeded {len(data)} reviews into sample_retail_07.reviews")

if __name__ == "__main__":
    print("Running seed script. Ensure DOCUMENTDB_URI is set in the environment.")
    asyncio.run(seed_db())
