from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from app.db import get_collection
from pymongo import UpdateOne
import math

app = FastAPI(title="DocumentDB Options Chain Ingest Sample")

BATCH_SIZE = 1000
COLLECTION_NAME = "options"


class OptionItem(BaseModel):
    strike: float
    optionType: str = Field(..., regex="^(call|put)$")
    bid: Optional[float]
    ask: Optional[float]
    lastPrice: Optional[float]
    timestamp: Optional[datetime]
    metadata: Optional[dict]


class IngestSnapshot(BaseModel):
    underlying: str
    expiry: date
    options: List[OptionItem]


@app.post("/ingest")
def ingest(snapshot: IngestSnapshot):
    coll = get_collection(COLLECTION_NAME)
    ops = []
    for opt in snapshot.options:
        doc = {
            "underlying": snapshot.underlying,
            "expiry": datetime.combine(snapshot.expiry, datetime.min.time()),
            "strike": opt.strike,
            "optionType": opt.optionType,
            "bid": opt.bid,
            "ask": opt.ask,
            "lastPrice": opt.lastPrice,
            "timestamp": opt.timestamp or datetime.utcnow(),
        }
        if opt.metadata:
            doc["metadata"] = opt.metadata
        # Use UpdateOne upsert to be idempotent: key by underlying+expiry+strike+optionType
        filter_doc = {"underlying": doc["underlying"], "expiry": doc["expiry"], "strike": doc["strike"], "optionType": doc["optionType"]}
        ops.append(UpdateOne(filter_doc, {"$set": doc}, upsert=True))

    # Execute in batches
    total = len(ops)
    for i in range(0, total, BATCH_SIZE):
        batch = ops[i:i+BATCH_SIZE]
        res = coll.bulk_write(batch, ordered=False)
    return {"status": "ok", "inserted_or_updated": total}


@app.get("/chains")
def get_chain(underlying: str = Query(...), expiry: date = Query(...)):
    coll = get_collection(COLLECTION_NAME)
    expiry_dt = datetime.combine(expiry, datetime.min.time())
    cursor = coll.find({"underlying": underlying, "expiry": expiry_dt}).sort("strike", 1)
    results = []
    for d in cursor:
        d["_id"] = str(d.get("_id"))
        # convert expiry to isoformat date
        if isinstance(d.get("expiry"), datetime):
            d["expiry"] = d["expiry"].date().isoformat()
        results.append(d)
    return results
