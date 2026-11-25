"""Fix index naming to avoid Beanie index creation conflicts."""
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

load_dotenv()
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DOCUMENTDB_DB", "sample_banking_15")

async def fix():
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    db = client[DATABASE_NAME]
    coll = db["onboarding_applications"]
    # drop the idx_applicant_id if it exists
    indexes = await coll.index_information()
    if "idx_applicant_id" in indexes:
        await coll.drop_index("idx_applicant_id")
    # create index with default naming
    await coll.create_index([("applicant_id", 1)])
    print("Fixed indexes")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix())
