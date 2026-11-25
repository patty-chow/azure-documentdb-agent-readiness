import asyncio
import os
from .db import get_motor_client
from dotenv import load_dotenv

load_dotenv()
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_retail_07")

async def create_indexes():
    client = get_motor_client()
    db = client[DATABASE_NAME]
    # Single-field index on product_id
    await db.reviews.create_index([("product_id", 1)], name="idx_product_id")
    # Compound index on product_id + sentiment_score
    await db.reviews.create_index([("product_id", 1), ("sentiment_score", 1)], name="idx_product_sentiment")
    print("Indexes created: idx_product_id, idx_product_sentiment")

if __name__ == "__main__":
    asyncio.run(create_indexes())
