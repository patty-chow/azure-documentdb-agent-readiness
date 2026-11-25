import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models import Report

_client = None

async def init_db():
    global _client
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
    # Create a singleton Motor client (reuse across module)
    if _client is None:
        _client = AsyncIOMotorClient(uri)
    db_name = os.environ.get("DOCUMENTDB_DB", "sample_fintech_10")
    db = _client[db_name]
    # Initialize Beanie with our document models
    await init_beanie(database=db, document_models=[Report])
    return _client

def get_client():
    return _client
