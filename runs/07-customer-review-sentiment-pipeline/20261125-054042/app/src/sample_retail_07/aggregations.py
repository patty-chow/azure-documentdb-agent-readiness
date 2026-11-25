import asyncio
import os
from dotenv import load_dotenv

from .db import init_db, get_motor_client

load_dotenv()
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_retail_07")

async def summary_by_product_and_sentiment():
    await init_db()
    client = get_motor_client()
    db = client[DATABASE_NAME]
    pipeline = [
        {"$project": {"product_id": 1, "sentiment_label": 1}},
        {"$group": {"_id": {"product_id": "$product_id", "sentiment": "$sentiment_label"}, "count": {"$sum": 1}}},
        {"$sort": {"_id.product_id": 1, "_id.sentiment": 1}}
    ]
    rows = await db.reviews.aggregate(pipeline).to_list(length=100)
    for r in rows:
        pid = r["_id"]["product_id"]
        sentiment = r["_id"]["sentiment"]
        print(f"product={pid}\tsentiment={sentiment}\tcount={r['count']}")

if __name__ == "__main__":
    asyncio.run(summary_by_product_and_sentiment())
