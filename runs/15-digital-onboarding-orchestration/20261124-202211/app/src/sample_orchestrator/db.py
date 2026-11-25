import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
from .models import OnboardingApplication

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        uri = os.environ.get("DOCUMENTDB_URI")
        if not uri:
            raise RuntimeError("DOCUMENTDB_URI must be set in the environment")
        _client = AsyncIOMotorClient(uri)
    return _client


async def init_db():
    client = get_client()
    db_name = os.environ.get("DOCUMENTDB_DB", "sample_banking_15")
    await init_beanie(database=client[db_name], document_models=[OnboardingApplication])


def get_db_name() -> str:
    return os.environ.get("DOCUMENTDB_DB", "sample_banking_15")
