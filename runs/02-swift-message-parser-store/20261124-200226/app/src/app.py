from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
import asyncio
from .db import init_db, close_db, get_motor_client, DB_NAME
from .models import SwiftMessage, ParsedSwift
from .parser import parse_swift
from datetime import datetime

app = FastAPI(title="Azure DocumentDB SWIFT Ingest Sample")

class IngestRequest(BaseModel):
    messages: List[str]

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.post("/ingest", status_code=202)
async def ingest(request: IngestRequest):
    client = get_motor_client()
    coll = client[DB_NAME]["swift_messages"]
    parsed_docs = []
    for raw in request.messages:
        p = parse_swift(raw)
        if not p:
            continue
        try:
            value_date = None
            if p.value_date:
                value_date = datetime.combine(p.value_date, datetime.min.time())
            doc = {
                "message_id": p.message_id,
                "message_type": p.message_type,
                "raw_text": raw,
                "sender": p.sender,
                "receiver": p.receiver,
                "amount": p.amount,
                "currency": p.currency,
                "value_date": value_date,
                "parsed": p.parsed,
            }
            parsed_docs.append(doc)
        except Exception:
            continue
    if not parsed_docs:
        raise HTTPException(status_code=400, detail="No valid messages parsed")
    try:
        result = await coll.insert_many(parsed_docs, ordered=False)
        return {"inserted_count": len(result.inserted_ids)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/aggregations/daily-summary")
async def daily_summary():
    client = get_motor_client()
    coll = client[DB_NAME]["swift_messages"]
    pipeline = [
        {"$match": {"value_date": {"$ne": None}}},
        {"$group": {
            "_id": {"message_type": "$message_type", "value_date": "$value_date"},
            "count": {"$sum": 1},
            "total_amount": {"$sum": {"$ifNull": ["$amount", 0]}}
        }},
        {"$sort": {"_id.value_date": 1, "_id.message_type": 1}}
    ]
    cursor = coll.aggregate(pipeline)
    out = []
    async for doc in cursor:
        vd = doc["_id"]["value_date"]
        if hasattr(vd, "isoformat"):
            vd_s = vd.isoformat()
        else:
            vd_s = str(vd)
        out.append({
            "message_type": doc["_id"]["message_type"],
            "value_date": vd_s,
            "count": doc["count"],
            "total_amount": doc["total_amount"],
        })
    return out
