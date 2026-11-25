import os
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ensure repo root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_customer_360_11"
TTL_DAYS = int(os.getenv("TTL_DAYS", "365"))

async def seed():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI must be set in the environment")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    db = client[DB_NAME]
    coll = db["consents"]

    now = datetime.utcnow()
    retention = now + timedelta(days=TTL_DAYS)

    samples = [
        {
            "customer_id": "cust_001",
            "consentVersion": 1,
            "current_preferences": {"email": True, "sms": False},
            "history": [{"timestamp": now, "action": "create", "actor": "seed_script", "channels": {"email": True, "sms": False}}],
            "retention_date": retention,
        },
        {
            "customer_id": "cust_002",
            "consentVersion": 1,
            "current_preferences": {"email": False, "sms": True},
            "history": [{"timestamp": now, "action": "create", "actor": "seed_script", "channels": {"email": False, "sms": True}}],
            "retention_date": retention,
        },
        {
            "customer_id": "cust_003",
            "consentVersion": 1,
            "current_preferences": {"email": True, "sms": True, "push": True},
            "history": [{"timestamp": now, "action": "create", "actor": "seed_script", "channels": {"email": True, "sms": True, "push": True}}],
            "retention_date": retention,
        },
    ]

    for s in samples:
        existing = await coll.find_one({"customer_id": s["customer_id"]})
        if existing:
            print(f"Skipping existing {s['customer_id']}")
        else:
            await coll.insert_one(s)
            print(f"Inserted {s['customer_id']}")

    # ensure indexes
    await coll.create_index([("retention_date", 1)], expireAfterSeconds=0, name="ttl_retention_date")
    await coll.create_index([("customer_id", 1)], unique=True, name="ix_customer_id_unique")

    indexes = await coll.index_information()
    print("Indexes:")
    for name, info in indexes.items():
        print(name, info)

if __name__ == '__main__':
    asyncio.run(seed())
