import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

URI = os.environ.get("DOCUMENTDB_URI")
DB = os.environ.get("DOCUMENTDB_DB", "sample_banking_15")
if not URI:
    raise RuntimeError("DOCUMENTDB_URI must be set")

async def create():
    client = AsyncIOMotorClient(URI)
    coll = client[DB]["onboarding_applications"]
    print("Creating index on state")
    await coll.create_index([("state", 1)], name="idx_state")
    print("Creating compound index on applicant_id+state")
    await coll.create_index([("applicant_id", 1), ("state", 1)], name="idx_applicant_state")
    print("Indexes created")

if __name__ == '__main__':
    asyncio.run(create())
