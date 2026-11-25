import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models import RawNote, DeidNote

async def init_db():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise EnvironmentError("DOCUMENTDB_URI environment variable is required")
    client = AsyncIOMotorClient(uri, tls=True)
    # get_default_database() may raise if the connection string has no default DB
    try:
        db = client.get_default_database()
    except Exception:
        db = None
    if not db:
        db = client["sample_healthcare_09"]
    await init_beanie(database=db, document_models=[RawNote, DeidNote])
    return client

# helper for scripts
if __name__ == "__main__":
    asyncio.run(init_db())
