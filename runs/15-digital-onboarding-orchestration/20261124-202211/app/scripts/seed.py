import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

DB = os.environ.get("DOCUMENTDB_DB", "sample_banking_15")
URI = os.environ.get("DOCUMENTDB_URI")
if not URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in environment for seeding")

SAMPLE = [
    {"applicant_id": "applicant-1", "applicant_name": "Alice Example", "state": "INIT", "created_at": datetime.utcnow(), "history": []},
    {"applicant_id": "applicant-2", "applicant_name": "Bob Fail", "state": "INIT", "created_at": datetime.utcnow(), "history": []},
    {"applicant_id": "applicant-9", "applicant_name": "Carol Risky", "state": "INIT", "created_at": datetime.utcnow(), "history": []},
]


async def seed():
    client = AsyncIOMotorClient(URI)
    coll = client[DB]["onboarding_applications"]
    for doc in SAMPLE:
        await coll.replace_one({"applicant_id": doc["applicant_id"]}, doc, upsert=True)
    print("Seeded sample applications")


if __name__ == "__main__":
    asyncio.run(seed())
