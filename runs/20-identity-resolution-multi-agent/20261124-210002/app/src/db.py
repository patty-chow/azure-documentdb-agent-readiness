import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models import Profile, GoldenRecord, AuditEntry

CLIENT = None
BEANIE_OK = False

async def get_client():
    global CLIENT
    if CLIENT is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        CLIENT = AsyncIOMotorClient(uri)
    return CLIENT

async def init_db():
    global BEANIE_OK
    if BEANIE_OK:
        return
    client = await get_client()
    db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_20")
    db = client[db_name]
    try:
        await init_beanie(database=db, document_models=[Profile, GoldenRecord, AuditEntry])
        BEANIE_OK = True
    except Exception as e:
        # do not raise; allow callers to fallback to motor-based writes
        print("init_beanie failed:", e)
        BEANIE_OK = False
