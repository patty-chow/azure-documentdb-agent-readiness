import os
from fastapi import FastAPI, HTTPException
from typing import List
import asyncio

from .db import init_db, get_raw_client
from .models import Complaint
from .pipeline import enrich_complaint

app = FastAPI(title="Complaint Classifier API")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/classify-run")
async def classify_run(limit: int = 50):
    # Pull unclassified documents and run enrichment
    db = get_raw_client()
    if not db:
        raise HTTPException(status_code=500, detail="DB client not initialized")
    db_name = os.environ.get("DOCUMENTDB_DB_NAME", "sample_banking_14")
    coll = db[db_name]["complaints"]
    cursor = coll.find({"product_category": None}).limit(limit)
    enriched = []
    async for doc in cursor:
        # wrap into Beanie model and save
        complaint = Complaint.parse_obj(doc)
        enriched_doc = await enrich_complaint(coll, complaint)
        enriched.append(str(enriched_doc.id))
    return {"enriched_count": len(enriched), "ids": enriched}

@app.post("/search")
async def search(q: str, k: int = 5):
    # For demo: naive text-embedding then $search KNN via cosmosSearch — placeholder
    from .pipeline import embed_text
    embedding = await embed_text(q)
    # Use raw pymongo $search with cosmosSearch if supported by cluster
    db = get_raw_client()
    db_name = os.environ.get("DOCUMENTDB_DB_NAME", "sample_banking_14")
    coll = db[db_name]["complaints"]
    pipeline = [
        {"$search": {"knn": {"vector": embedding, "path": "embedding", "k": k}}},
        {"$project": {"complaint_text": 1, "score": {"$meta": "searchScore"}}},
    ]
    cursor = coll.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append({"text": doc.get("complaint_text"), "score": doc.get("score")})
    return {"results": results}

@app.get("/hotspots")
async def hotspots():
    db = get_raw_client()
    db_name = os.environ.get("DOCUMENTDB_DB_NAME", "sample_banking_14")
    coll = db[db_name]["complaints"]
    pipeline = [
        {"$group": {"_id": "$product_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    cursor = coll.aggregate(pipeline)
    out = []
    async for doc in cursor:
        out.append({"product_category": doc.get("_id"), "count": doc.get("count")})
    return {"hotspots": out}
