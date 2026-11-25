import os
import sys
import asyncio
from dotenv import load_dotenv

# ensure repo root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_customer_360_11"

async def inspect():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI must be set in the environment")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    db = client[DB_NAME]
    coll = db["consents"]
    indexes = await coll.index_information()
    print("Indexes:")
    for name, info in indexes.items():
        print(name, info)

if __name__ == '__main__':
    asyncio.run(inspect())
