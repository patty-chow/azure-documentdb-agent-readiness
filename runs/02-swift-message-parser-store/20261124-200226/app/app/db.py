import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models import SwiftMessage

DATABASE_NAME = "sample_banking_02"

_mongo_client: AsyncIOMotorClient | None = None

async def init_db():
    global _mongo_client
    uri = os.getenv("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI not set in environment")
    _mongo_client = AsyncIOMotorClient(uri)
    db = _mongo_client[DATABASE_NAME]
    # create indexes explicitly
    coll_name = SwiftMessage.Settings.name
    coll = db[coll_name]
    # unique index on message_id if present
    await coll.create_index("message_id", unique=False)
    await coll.create_index([("message_type", 1), ("value_date", 1)])
    await init_beanie(database=db, document_models=[SwiftMessage])

def get_client():
    if _mongo_client is None:
        raise RuntimeError("DB client not initialized")
    return _mongo_client
