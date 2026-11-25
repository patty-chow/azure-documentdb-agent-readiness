import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

from src.models import SurveyResponse

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_customer_360_17")

async def init_db():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI is not set in the environment")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    db = client[DATABASE_NAME]
    await init_beanie(database=db, document_models=[SurveyResponse])
    return client, db

if __name__ == "__main__":
    asyncio.run(init_db())
