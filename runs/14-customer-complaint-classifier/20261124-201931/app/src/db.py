import os
import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from .models import Complaint
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_banking_14")

# Singleton client per process (driver best practice)
_client: AsyncIOMotorClient | None = None

async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        # Motor client options: tune for long-running server
        _client = AsyncIOMotorClient(DOCUMENTDB_URI, tls=True)
    return _client

async def init_db():
    client = await get_client()
    db = client[DATABASE_NAME]
    await init_beanie(database=db, document_models=[Complaint])

# Utility to run init from sync entrypoints
def init_db_sync():
    asyncio.run(init_db())
