import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = "sample_customer_360_11"
TTL_DAYS = int(os.getenv("TTL_DAYS", "365"))

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in the environment")

app = FastAPI(title="Consent Preference Center (DocumentDB sample)")

# Models
class ConsentHistoryEntry(BaseModel):
    timestamp: datetime
    action: str  # e.g., 'grant', 'withdraw', 'update', 'create'
    actor: Optional[str]
    channels: Dict[str, bool]

class ConsentDocument(Document):
    customer_id: str = Field(...)
    consentVersion: int = 1
    current_preferences: Dict[str, bool] = Field(default_factory=dict)
    history: List[ConsentHistoryEntry] = Field(default_factory=list)
    retention_date: datetime

    class Settings:
        name = "consents"

# Pydantic bodies
class ConsentRequest(BaseModel):
    customer_id: str
    preferences: Dict[str, bool]
    actor: Optional[str] = None
    consentVersion: Optional[int] = None

class WithdrawRequest(BaseModel):
    customer_id: str
    channels: Optional[List[str]] = None  # if None, withdraw all
    actor: Optional[str] = None

# DB client and initialization
client: Optional[AsyncIOMotorClient] = None

@app.on_event("startup")
async def startup_event():
    global client
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    await init_beanie(database=client[DB_NAME], document_models=[ConsentDocument])

    # ensure indexes: TTL on retention_date and unique index on customer_id
    coll = ConsentDocument.get_motor_collection()
    # TTL index: expireAt semantics when expireAfterSeconds=0
    await coll.create_index([("retention_date", 1)], expireAfterSeconds=0, name="ttl_retention_date")
    # Unique index on customer_id for one doc per customer
    await coll.create_index([("customer_id", 1)], unique=True, name="ix_customer_id_unique")

@app.post("/consent")
async def record_consent(req: ConsentRequest):
    # upsert behavior: if exists, append history and update
    now = datetime.utcnow()
    retention = now + timedelta(days=TTL_DAYS)

    existing = await ConsentDocument.find_one({"customer_id": req.customer_id})
    history_entry = ConsentHistoryEntry(timestamp=now, action="grant", actor=req.actor, channels=req.preferences)

    if existing:
        # update version
        existing.consentVersion = (req.consentVersion or existing.consentVersion) + 1
        # merge/update preferences
        existing.current_preferences.update(req.preferences)
        existing.history.append(history_entry)
        existing.retention_date = retention
        await existing.save()
        return {"status": "updated", "customer_id": existing.customer_id, "consentVersion": existing.consentVersion, "current_preferences": existing.current_preferences}
    else:
        doc = ConsentDocument(
            customer_id=req.customer_id,
            consentVersion=req.consentVersion or 1,
            current_preferences=req.preferences,
            history=[history_entry],
            retention_date=retention,
        )
        try:
            await doc.insert()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"status": "created", "customer_id": doc.customer_id, "consentVersion": doc.consentVersion, "current_preferences": doc.current_preferences}

@app.post("/consent/withdraw")
async def withdraw_consent(req: WithdrawRequest):
    now = datetime.utcnow()
    retention = now + timedelta(days=TTL_DAYS)

    existing = await ConsentDocument.find_one({"customer_id": req.customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="consent not found")

    # determine channels to withdraw
    if req.channels is None:
        channels = {k: False for k in existing.current_preferences.keys()}
    else:
        channels = {ch: False for ch in req.channels}

    history_entry = ConsentHistoryEntry(timestamp=now, action="withdraw", actor=req.actor, channels=channels)
    existing.current_preferences.update(channels)
    existing.history.append(history_entry)
    existing.consentVersion += 1
    existing.retention_date = retention
    await existing.save()
    return {"status": "withdrawn", "customer_id": existing.customer_id, "consentVersion": existing.consentVersion, "current_preferences": existing.current_preferences}

@app.get("/consent/{customer_id}")
async def get_consent(customer_id: str):
    existing = await ConsentDocument.find_one({"customer_id": customer_id})
    if not existing:
        raise HTTPException(status_code=404, detail="consent not found")
    # Return the current preference state
    return {"customer_id": existing.customer_id, "consentVersion": existing.consentVersion, "current_preferences": existing.current_preferences, "history": [h.dict() for h in existing.history]}

# small run helper when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
