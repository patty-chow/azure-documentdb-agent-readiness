import os
import math
import numpy as np
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

load_dotenv()

from app.models import Product, ProductPair, Order

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_retail_19")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

app = FastAPI(title="Cross-sell recommendation sample")

# Module-scoped client & db
_mongo_client: AsyncIOMotorClient | None = None
_beanie_initialized = False

class BasketRequest(BaseModel):
    basket: List[str]

@app.on_event("startup")
async def startup_event():
    global _mongo_client, _beanie_initialized
    if not DOCUMENTDB_URI:
        # For unit tests and quick validation, allow startup to proceed without a live cluster.
        # Full integration requires DOCUMENTDB_URI to be set; the README explains this.
        _beanie_initialized = False
        return
    # Singleton client per process (driver best-practice)
    _mongo_client = AsyncIOMotorClient(DOCUMENTDB_URI)
    # Initialize Beanie with our documents
    await init_beanie(database=_mongo_client[DATABASE_NAME], document_models=[Product, ProductPair, Order])
    _beanie_initialized = True

def _normalize(v: List[float]) -> List[float]:
    a = np.array(v, dtype=float)
    norm = np.linalg.norm(a)
    if norm == 0:
        return a.tolist()
    return (a / norm).tolist()

def _cosine(a: List[float], b: List[float]) -> float:
    a2 = np.array(a, dtype=float)
    b2 = np.array(b, dtype=float)
    if a2.size == 0 or b2.size == 0:
        return 0.0
    denom = (np.linalg.norm(a2) * np.linalg.norm(b2))
    if denom == 0:
        return 0.0
    return float(np.dot(a2, b2) / denom)

@app.post("/cross-sell")
async def cross_sell(req: BasketRequest):
    basket = list(dict.fromkeys(req.basket))  # dedupe preserving order
    if not basket:
        raise HTTPException(status_code=400, detail="basket must contain at least one product id")

    if not _beanie_initialized:
        # For quick runs without a DB, surface a clear error
        raise HTTPException(status_code=503, detail="Database not initialized; set DOCUMENTDB_URI to run cross-sell")

    # Fetch product embeddings for basket items
    products = await Product.find({"_id": {"$in": basket}}).to_list()
    if not products:
        raise HTTPException(status_code=404, detail="No products found for basket ids")

    # Build basket embedding = normalized average of product embeddings
    embeddings = [p.embedding for p in products if p.embedding]
    if not embeddings:
        raise HTTPException(status_code=500, detail="Basket product embeddings not available; run seed to generate embeddings")

    avg = np.mean(np.array(embeddings, dtype=float), axis=0).tolist()
    basket_emb = _normalize(avg)

    # Find candidate pairs that include any basket product
    cursor = ProductPair.find({"product_ids": {"$in": basket}})
    pairs = await cursor.to_list()

    # Score candidates: for each pair, pick the other product id as candidate
    scores = {}
    max_log_count = 0.0
    temp = []
    for p in pairs:
        if not p.embedding:
            continue
        # find other id(s)
        others = [pid for pid in p.product_ids if pid not in basket]
        if not others:
            continue
        sim = _cosine(basket_emb, p.embedding)
        log_count = math.log1p(p.count)
        if log_count > max_log_count:
            max_log_count = log_count
        temp.append((p, others, sim, log_count))

    # Normalize log_count and compute affinity
    for p, others, sim, log_count in temp:
        norm_count = (log_count / max_log_count) if max_log_count > 0 else 0.0
        affinity = 0.7 * max(0.0, sim) + 0.3 * norm_count
        for o in others:
            if o in basket:
                continue
            if o not in scores or scores[o] < affinity:
                scores[o] = affinity

    # Return top 5 candidates
    result = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return {"candidates": [{"product_id": pid, "score": float(score)} for pid, score in result]}
