import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_banking_02"

async def run():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    coll = client[DB_NAME]["swift_messages"]
    pipeline = [
        {"$match": {"value_date": {"$ne": None}}},
        {"$group": {
            "_id": {"message_type": "$message_type", "value_date": "$value_date"},
            "count": {"$sum": 1},
            "total_amount": {"$sum": {"$ifNull": ["$amount", 0]}}
        }},
        {"$sort": {"_id.value_date": 1, "_id.message_type": 1}}
    ]
    rows = []
    cursor = coll.aggregate(pipeline)
    async for d in cursor:
        rows.append(d)
    for r in rows:
        print(r)
    client.close()

if __name__ == '__main__':
    asyncio.run(run())
