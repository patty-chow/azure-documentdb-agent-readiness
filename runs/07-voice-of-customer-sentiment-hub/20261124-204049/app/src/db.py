import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = os.getenv("DB_NAME", "sample_customer_360_07")

_client = None

async def get_client():
    global _client
    if _client is None:
        # Ensure TLS and retryWrites per readiness guidance
        _client = AsyncIOMotorClient(DOCUMENTDB_URI, tls=True, retryWrites=False)
    return _client

async def init_db(models):
    client = await get_client()
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=models)
    return db
