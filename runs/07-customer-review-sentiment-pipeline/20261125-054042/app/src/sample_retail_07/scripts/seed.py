import asyncio
import json
import os
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from ..db import init_db
from ..models import Review

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_reviews.json")

async def seed():
    await init_db()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    # Upsert by review_id (idempotent)
    for doc in docs:
        # ensure datetime objects
        doc.setdefault("created_at", datetime.utcnow().isoformat())
        filter_q = {"review_id": doc["review_id"]}
        await Review.find_one(filter_q).upsert({"$setOnInsert": doc})
    print(f"Seeded {len(docs)} documents (upserted where missing)")

if __name__ == "__main__":
    asyncio.run(seed())
