#!/usr/bin/env python3
"""Run an aggregation: counts grouped by product_id and sentiment_label"""
import sys
import asyncio
from pathlib import Path
# ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sample_retail_07.db import init_db
from src.sample_retail_07.models import Review

async def run_agg():
    await init_db()
    pipeline = [
        {"$group": {"_id": {"product_id": "$product_id", "sentiment_label": "$sentiment_label"}, "count": {"$sum": 1}}},
        {"$sort": {"_id.product_id": 1, "_id.sentiment_label": 1}}
    ]
    cursor = Review.get_motor_collection().aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(doc)
    for r in results:
        pid = r["_id"]["product_id"]
        label = r["_id"].get("sentiment_label")
        print(f"product={pid}\tsentiment={label}\tcount={r['count']}")

if __name__ == "__main__":
    asyncio.run(run_agg())
