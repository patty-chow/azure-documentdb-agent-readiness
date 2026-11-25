import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models import SwiftMessage
import asyncio

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_banking_02"

_client: AsyncIOMotorClient | None = None

def get_motor_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable not set")
        # Default pool sizes left to driver defaults; caller can tune via query params
        _client = AsyncIOMotorClient(DOCUMENTDB_URI)
    return _client

async def init_db():
    client = get_motor_client()
    await init_beanie(database=client[DB_NAME], document_models=[SwiftMessage])

async def close_db():
    global _client
    if _client is not None:
        _client.close()
        _client = None
