import os
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from .models import Complaint

async_client = None

async def init_db():
    global async_client
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI not set in environment")
    # Use recommended connection options for DocumentDB
    async_client = AsyncIOMotorClient(uri)
    db_name = os.environ.get("DOCUMENTDB_DB_NAME", "sample_banking_14")
    await init_beanie(database=async_client[db_name], document_models=[Complaint])

def get_raw_client():
    return async_client
