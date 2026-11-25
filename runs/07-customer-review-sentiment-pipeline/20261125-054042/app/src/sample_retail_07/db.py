import os
import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from .models import Review

DOCUMENTDB_URI_ENV = "DOCUMENTDB_URI"
DB_NAME = "sample_retail_07"

async def init_db():
    uri = os.getenv(DOCUMENTDB_URI_ENV)
    if not uri:
        raise RuntimeError(f"Environment variable {DOCUMENTDB_URI_ENV} is required")
    client = AsyncIOMotorClient(uri)
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[Review])
    return db

# helper to close client (beanie does not expose client directly)
async def close_db(client: AsyncIOMotorClient):
    client.close()
