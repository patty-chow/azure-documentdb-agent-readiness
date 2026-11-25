from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
from .db import init_db
from .parser import parse_swift
from .models import SwiftMessage
from .utils import normalize_doc_for_insert

app = FastAPI(title="Azure DocumentDB SWIFT Ingest Sample")

class RawMessage(BaseModel):
    raw: str

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.post("/ingest")
async def ingest(messages: List[RawMessage]):
    # parse and validate
    docs = []
    errors = []
    for i, m in enumerate(messages):
        parsed = parse_swift(m.raw)
        try:
            doc = SwiftMessage(**parsed)
            docs.append(normalize_doc_for_insert(doc.dict(exclude_none=True)))
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    if not docs:
        raise HTTPException(status_code=400, detail={"errors": errors})
    # bulk insert using motor collection
    coll = SwiftMessage.get_motor_collection()
    res = await coll.insert_many(docs)
    inserted_count = len(res.inserted_ids) if hasattr(res, 'inserted_ids') else len(docs)
    return {"inserted_count": inserted_count, "errors": errors}

@app.get("/aggregations/daily-summary")
async def daily_summary():
    # use underlying collection to run aggregation
    pipeline = [
        {"$match": {"message_type": {"$in": ["MT103", "MT202"]}}},
        {"$group": {
            "_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$value_date"}}, "message_type": "$message_type"},
            "count": {"$sum": 1},
            "total_amount": {"$sum": {"$ifNull": ["$amount", 0]}}
        }},
        {"$project": {"date": "$_id.date", "message_type": "$_id.message_type", "count": 1, "total_amount": 1, "_id": 0}},
        {"$sort": {"date": 1, "message_type": 1}}
    ]
    coll = SwiftMessage.get_motor_collection()
    cursor = coll.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(doc)
    return results
