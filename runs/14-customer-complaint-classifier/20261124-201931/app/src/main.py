import os
import asyncio
from fastapi import FastAPI, HTTPException
from typing import List
from dotenv import load_dotenv
from .db import init_db
from .models import Complaint
from .pipeline import run_classify

load_dotenv()
app = FastAPI(title="Complaint Classifier")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/classify-run")
def classify_run(limit: int = 50):
    try:
        updated = run_classify(limit=limit)
        return {"updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(query: str, k: int = 5):
    # simple in-app embedding + brute-force similarity for demo
    from .pipeline import embed_text
    import numpy as np
    emb = asyncio.run(embed_text(query))
    if not emb:
        raise HTTPException(status_code=500, detail="Embedding failed")

    # fetch docs with embeddings
    docs = await Complaint.find(Complaint.embedding != None).to_list()
    def score(d):
        a = np.array(d.embedding)
        b = np.array(emb)
        # cosine similarity
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
        return sim
    docs_sorted = sorted(docs, key=score, reverse=True)[:k]
    return [{"id": str(d.id), "external_id": d.external_id, "score": score(d), "product_category": d.product_category} for d in docs_sorted]

@app.get("/hotspots")
async def hotspots():
    # aggregation by product_category
    pipeline = [
        {"$group": {"_id": "$product_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    client = Complaint.get_motor_collection().database.client
    db = client[os.environ.get("DATABASE_NAME", "sample_banking_14")]
    res = await db["complaints"].aggregate(pipeline).to_list(length=100)
    return res
