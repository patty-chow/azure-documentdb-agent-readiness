import os
import asyncio
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional

load_dotenv()
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .models import Consent, HistoryItem
from .schemas import RecordConsentRequest, WithdrawConsentRequest, ConsentResponse

DB_NAME = "sample_customer_360_11"
DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
RETENTION_DAYS = int(os.getenv("CONSENT_RETENTION_DAYS", "365"))

app = FastAPI(title="Consent Preference Center")

client: Optional[AsyncIOMotorClient] = None

async def init_db():
    global client
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI environment variable must be set to connect to DocumentDB")
    client = AsyncIOMotorClient(DOCUMENTDB_URI)
    await init_beanie(database=client[DB_NAME], document_models=[Consent])
    # Ensure TTL index on retention_expires_at with expireAfterSeconds=0
    await client[DB_NAME][Consent.Collection.name].create_index("retention_expires_at", expireAfterSeconds=0, name="ttl_retention_expires_at")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/consents/record", response_model=ConsentResponse)
async def record_consent(req: RecordConsentRequest):
    # Upsert by customerId: append a history item and set channels + version
    now = datetime.utcnow()
    retention = now + timedelta(days=RETENTION_DAYS)
    consent = await Consent.find_one(Consent.customerId == req.customerId)
    if consent is None:
        consent = Consent(customerId=req.customerId, consentVersion=1, channels=req.channels, history=[], retention_expires_at=retention)
    else:
        consent.consentVersion += 1
        consent.channels = {**consent.channels, **req.channels}
        consent.retention_expires_at = retention
    history_item = HistoryItem(action="grant", channels=req.channels, version=consent.consentVersion, actor=req.actor, reason=req.reason)
    consent.history.append(history_item)
    await consent.save()
    return ConsentResponse(customerId=consent.customerId, consentVersion=consent.consentVersion, channels=consent.channels)

@app.post("/consents/withdraw", response_model=ConsentResponse)
async def withdraw_consent(req: WithdrawConsentRequest):
    now = datetime.utcnow()
    retention = now + timedelta(days=RETENTION_DAYS)
    consent = await Consent.find_one(Consent.customerId == req.customerId)
    if consent is None:
        raise HTTPException(status_code=404, detail="Consent not found for customer")
    consent.consentVersion += 1
    if req.channels is None:
        # withdraw all
        consent.channels = {k: False for k in consent.channels.keys()}
        channels_changed = consent.channels
    else:
        for k, v in req.channels.items():
            consent.channels[k] = v
        channels_changed = req.channels
    consent.retention_expires_at = retention
    history_item = HistoryItem(action="withdraw", channels=channels_changed, version=consent.consentVersion, actor=req.actor, reason=req.reason)
    consent.history.append(history_item)
    await consent.save()
    return ConsentResponse(customerId=consent.customerId, consentVersion=consent.consentVersion, channels=consent.channels)

@app.get("/consents/{customerId}", response_model=ConsentResponse)
async def get_consent(customerId: str):
    consent = await Consent.find_one(Consent.customerId == customerId)
    if consent is None:
        raise HTTPException(status_code=404, detail="Consent not found")
    return ConsentResponse(customerId=consent.customerId, consentVersion=consent.consentVersion, channels=consent.channels)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
