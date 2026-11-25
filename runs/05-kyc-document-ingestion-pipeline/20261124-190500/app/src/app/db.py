from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from .models import Customer

_client = None

def get_mongo_uri():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
    return uri

async def init_db():
    global _client
    uri = get_mongo_uri()
    # DocumentDB (Azure) requires TLS; connection string should include tls=true
    # Use Motor's AsyncIOMotorClient as Beanie expects
    _client = AsyncIOMotorClient(uri)
    # Initialize Beanie with our document models
    await init_beanie(database=_client.get_default_database(), document_models=[Customer])

async def get_db_client():
    if _client is None:
        raise RuntimeError("DB client not initialized. Call init_db() first.")
    return _client
