"""API routes for product substitute lookup and simple product retrieval.

This module implements a /substitute endpoint that accepts a product_id and returns the
closest alternatives based on vector similarity. For clarity, the implementation uses a
MongoDB aggregation with a $search stage (knn-like) if the server supports it; otherwise
it falls back to fetching embeddings and computing cosine similarity client-side.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from .models import Product


router = APIRouter()


class SubstituteResult(BaseModel):
    """Result returned by /substitute endpoint for each alternative product."""

    product_id: str
    name: str
    score: float


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors a and b.

    Returns -1..1 where 1 means identical direction. The function handles zero vectors
    gracefully by returning -1.0 (lowest similarity).
    """
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    if np.linalg.norm(a_arr) == 0 or np.linalg.norm(b_arr) == 0:
        return -1.0
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


@router.get("/substitute/{product_id}", response_model=List[SubstituteResult])
async def find_substitutes(product_id: str, k: int = 5) -> List[SubstituteResult]:
    """Find up to k nearest product substitutes for the given product_id.

    Steps performed:
    1. Lookup the product by product_id and read its embedding.
    2. Attempt a server-side vector search using a $search aggregation stage (knnBeta style).
       If the server does not support this stage or it fails, fall back to a client-side
       nearest-neighbors computation by scanning embeddings (works but is less efficient).

    Returns a list of SubstituteResult with the product_id, name and similarity score.
    """
    # Find the product in the DB
    prod = await Product.find_one(Product.product_id == product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    query_vec = prod.embedding
    if not query_vec:
        raise HTTPException(status_code=400, detail="Product has no embedding to compare")

    # Attempt server-side vector search using an aggregation pipeline that relies on $search/knn.
    # This is the preferred path when the DocumentDB cluster supports vector search indexes.
    try:
        db = Product.get_motor_collection().database
        # Aggregation pipeline with a $search stage. The exact operator names (knnBeta) match
        # the $search knn-style syntax used by many vector search integrations. If the server
        # supports it, this will return the best matches directly from the server.
        pipeline = [
            {
                "$search": {
                    "knnBeta": {
                        "vector": query_vec,
                        "path": "embedding",
                        "k": k + 1,  # request one extra to allow excluding the same product
                    }
                }
            },
            {"$limit": k + 1},
            {"$project": {"product_id": 1, "name": 1, "score": {"$meta": "searchScore"}}},
        ]
        cursor = db[Product.get_motor_collection().name].aggregate(pipeline)
        results = []
        async for doc in cursor:
            # Skip the input product if returned in results
            if doc.get("product_id") == product_id:
                continue
            results.append(SubstituteResult(product_id=doc.get("product_id"), name=doc.get("name"), score=doc.get("score", 0.0)))
            if len(results) >= k:
                break

        if results:
            return results
    except Exception:
        # If server-side vector search is not available, fall back to client-side computation.
        pass

    # Client-side fallback: load candidate embeddings and compute cosine similarity.
    # Note: This performs a collection scan and is only suitable for small datasets or dev samples.
    candidates = Product.find_all()
    sims = []
    async for c in candidates:
        if c.product_id == product_id:
            continue
        if not c.embedding:
            continue
        score = _cosine_similarity(query_vec, c.embedding)
        sims.append((score, c))

    sims.sort(key=lambda x: x[0], reverse=True)
    results = [SubstituteResult(product_id=p.product_id, name=p.name, score=float(score)) for score, p in sims[:k]]
    return results


@router.get("/product/{product_id}")
async def get_product(product_id: str):
    """Return a single product document by product_id for UI use."""
    prod = await Product.find_one(Product.product_id == product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Not found")
    return prod
