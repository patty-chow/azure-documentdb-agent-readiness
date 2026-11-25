import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from src.db import get_client, init_db
from src.models import Feedback

async def agg_by_channel():
    await init_db([Feedback])
    cursor = Feedback.get_motor_collection().aggregate([
        {"$group": {"_id": "$channel", "avgSentiment": {"$avg": "$sentiment"}, "count": {"$sum": 1}}},
        {"$sort": {"avgSentiment": -1}}
    ])
    print('\nSentiment by channel:')
    async for doc in cursor:
        print(doc)

async def agg_by_topic():
    await init_db([Feedback])
    cursor = Feedback.get_motor_collection().aggregate([
        {"$unwind": {"path": "$topics", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$topics", "avgSentiment": {"$avg": "$sentiment"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    print('\nSentiment by topic:')
    async for doc in cursor:
        print(doc)

async def agg_by_day():
    await init_db([Feedback])
    cursor = Feedback.get_motor_collection().aggregate([
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "avgSentiment": {"$avg": "$sentiment"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])
    print('\nSentiment by day:')
    async for doc in cursor:
        print(doc)

async def main():
    await agg_by_channel()
    await agg_by_topic()
    await agg_by_day()

if __name__ == '__main__':
    asyncio.run(main())
