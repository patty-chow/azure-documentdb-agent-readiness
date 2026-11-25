import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from .models import LabResult

DB_NAME = "sample_healthcare_07"

def normalized_uri(uri: str) -> str:
    # Ensure required query params exist per readiness guidance: tls=true, authMechanism=SCRAM-SHA-256, retryWrites=false
    if not uri:
        raise ValueError("DOCUMENTDB_URI is empty")
    # Quick and simple append if missing
    if "?" in uri:
        sep = "&"
    else:
        sep = "?"
    additions = []
    if "tls=" not in uri and "ssl=" not in uri:
        additions.append("tls=true")
    if "authMechanism=" not in uri:
        additions.append("authMechanism=SCRAM-SHA-256")
    if "retryWrites=" not in uri:
        additions.append("retryWrites=false")
    if additions:
        uri = uri + sep + "&".join(additions)
    return uri

_client: Optional[AsyncIOMotorClient] = None

async def get_client():
    global _client
    if _client is None:
        raw = os.getenv("DOCUMENTDB_URI")
        if not raw:
            raise RuntimeError("DOCUMENTDB_URI environment variable not set")
        uri = normalized_uri(raw)
        # Motor will manage a pool inside AsyncIOMotorClient; follow singleton pattern
        _client = AsyncIOMotorClient(uri)
    return _client

async def init_db():
    client = await get_client()
    await init_beanie(database=client[DB_NAME], document_models=[LabResult])

async def create_compound_index():
    client = await get_client()
    coll = client[DB_NAME]["lab_results"]
    # Compound index: {patientId:1, testCode:1, timestamp:1}
    await coll.create_index([("patientId", 1), ("testCode", 1), ("timestamp", 1)])

if __name__ == "__main__":
    asyncio.run(init_db())
