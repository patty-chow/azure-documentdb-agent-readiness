import os
import asyncio
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from beanie import init_beanie
from pymongo import IndexModel, ASCENDING
from pymongo.errors import PyMongoError
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

from src.models import AdverseEvent

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DATABASE = os.getenv("DOCUMENTDB_DATABASE", "sample_healthcare_18")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Adverse Event Reporting (DocumentDB + Beanie)")

class ReportIn(BaseModel):
    text: str

class AggregationOut(BaseModel):
    drug: str
    event: str
    count: int

@app.on_event("startup")
async def startup():
    if DOCUMENTDB_URI is None:
        raise RuntimeError("DOCUMENTDB_URI environment variable is required")
    # Use PyMongo AsyncMongoClient per Beanie 2 quickstart
    from pymongo import MongoClient
    client = MongoClient(DOCUMENTDB_URI)
    db = client[DATABASE]
    # Initialize Beanie (uses async driver internally)
    await init_beanie(database=db, document_models=[AdverseEvent])
    # Ensure compound index on (drug, event)
    try:
        coll = db[AdverseEvent.get_motor_collection().name]
        coll.create_index([("drug", ASCENDING), ("event", ASCENDING)], name="idx_drug_event")
    except PyMongoError as e:
        print("Warning: failed to create index:", e)

@app.post("/reports", response_model=dict)
async def create_report(report: ReportIn):
    # If OPENAI_API_KEY is configured, attempt extraction using OpenAI; otherwise, return an error
    parsed = None
    if OPENAI_API_KEY:
        parsed = await extract_with_openai(report.text)
    else:
        raise HTTPException(status_code=400, detail="LLM extraction disabled; set OPENAI_API_KEY or use seed.py fallback")
    if not parsed:
        raise HTTPException(status_code=400, detail="Failed to parse report")
    # Validate and save with Beanie
    ae = AdverseEvent(**parsed, raw_text=report.text)
    await ae.insert()
    return {"id": str(ae.id)}

@app.get("/reports/top-events", response_model=List[AggregationOut])
async def top_events(limit: int = 50):
    # Aggregation: group by drug and event and count
    pipeline = [
        {"$group": {"_id": {"drug": "$drug", "event": "$event"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "drug": "$_id.drug", "event": "$_id.event", "count": 1}}
    ]
    coll = AdverseEvent.get_motor_collection()
    cursor = coll.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(AggregationOut(**doc))
    return results

# Minimal OpenAI extraction helper (async)
async def extract_with_openai(text: str):
    import openai
    openai.api_key = OPENAI_API_KEY
    prompt = (
        "Extract these fields from the following adverse event free-text report:\n"
        "Return a JSON object with keys: drug, event, severity, onset_date (YYYY-MM-DD or null)."
        "If a field is missing, set it to null. Do not add other keys.\n\n"
        f"Report:\n{text}\n\nJSON:\n"
    )
    try:
        # Use completion-like API (ChatCompletion) synchronously via openai; call in thread to avoid blocking
        from functools import partial
        def call():
            return openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, call)
        content = resp["choices"][0]["message"]["content"].strip()
        import json
        parsed = json.loads(content)
        # Basic normalization: ensure keys exist
        return {
            "drug": parsed.get("drug"),
            "event": parsed.get("event"),
            "severity": parsed.get("severity"),
            "onset_date": parsed.get("onset_date")
        }
    except Exception as e:
        print("Extraction failed:", e)
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
