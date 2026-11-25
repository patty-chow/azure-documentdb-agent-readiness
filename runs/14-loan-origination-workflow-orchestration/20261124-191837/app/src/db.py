import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = "sample_fintech_14"

# Singleton client per driver best-practices
_client: AsyncIOMotorClient | None = None

async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI not set in environment")
        # Use Motor client
        _client = AsyncIOMotorClient(DOCUMENTDB_URI)
    return _client

async def init_db(models):
    client = await get_client()
    await init_beanie(database=client.get_database(DB_NAME), document_models=models)

async def close_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None
