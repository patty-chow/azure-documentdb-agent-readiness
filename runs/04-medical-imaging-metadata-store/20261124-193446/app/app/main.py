from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
import numpy as np
from typing import List
from app.db import get_collection

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "medical_images")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Medical Imaging Metadata Store")

class SearchResult(BaseModel):
    _id: str
    modality: str
    body_part: str
    findings: str
    score: float


def embed_text(text: str) -> List[float]:
    if OPENAI_API_KEY:
        resp = openai.Embeddings.create(input=text, model=OPENAI_MODEL)
        vec = resp["data"][0]["embedding"]
        # Normalize for cosine similarity
        arr = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = (arr / norm).astype(float)
        return arr.tolist()
    else:
        # deterministic pseudo-embedding for demo when no API key is present
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        arr = rng.normal(size=(EMBEDDING_DIM,)).astype(np.float32)
        arr = arr / np.linalg.norm(arr)
        return arr.tolist()


@app.get("/search", response_model=List[SearchResult])
def search(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=100)):
    # compute embedding
    try:
        qvec = embed_text(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

    # build aggregation pipeline using cosmosSearch knn
    collection = get_collection(COLLECTION_NAME)

    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "path": "embedding",
                    "vector": qvec,
                    "k": k,
                    "lSearch": max(40, k * 4)
                }
            }
        },
        {
            "$project": {
                "modality": 1,
                "body_part": 1,
                "findings": 1,
                "score": {"$meta": "searchScore"}
            }
        },
    ]

    try:
        cursor = collection.aggregate(pipeline)
        results = []
        for doc in cursor:
            results.append(
                SearchResult(
                    _id=str(doc.get("_id")),
                    modality=doc.get("modality"),
                    body_part=doc.get("body_part"),
                    findings=doc.get("findings"),
                    score=float(doc.get("score", 0.0)),
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {e}")
