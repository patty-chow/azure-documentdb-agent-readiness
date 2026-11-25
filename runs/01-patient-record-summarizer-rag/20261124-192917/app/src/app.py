from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from src.db import get_db
import os

load_dotenv()

app = FastAPI(title="Patient Record Summarizer (RAG)")

class SearchRequest(BaseModel):
    patientId: str
    question: str
    k: int = 5

class SourceChunk(BaseModel):
    _id: str
    patientId: str
    chunkId: int
    score: float
    text: str

class SearchResponse(BaseModel):
    summary: str
    sources: List[SourceChunk]


@app.post('/search', response_model=SearchResponse)
def search(req: SearchRequest):
    db = get_db()
    coll = db['patient_chunks']
    # The real app would call embedding provider and LLM here. For sample inclusion we reuse scripts/query.search pipeline.
    from scripts.query import embed_text
    qv = embed_text(req.question)
    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "path": "embedding",
                    "vector": qv,
                    "k": req.k,
                    "lSearch": max(50, req.k*10),
                    "filter": {"patientId": {"$eq": req.patientId}}
                }
            }
        },
        {"$project": {"patientId": 1, "chunkId": 1, "text": 1, "score": {"$meta": "searchScore"}}}
    ]
    hits = list(coll.aggregate(pipeline))
    if not hits:
        raise HTTPException(404, "No relevant chunks found")
    # For brevity summarize by concatenating top-k texts. Real app should call LLM with prompt engineering.
    summary = "\n".join([h['text'] for h in hits])
    sources = []
    for h in hits:
        sources.append({
            "_id": str(h.get('_id')),
            "patientId": h.get('patientId'),
            "chunkId": h.get('chunkId'),
            "score": float(h.get('score', 0)),
            "text": h.get('text')
        })
    return {"summary": summary, "sources": sources}
