from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .store import DocumentStore
from .embeddings import get_embedding
from .summarizer import summarize

app = FastAPI(title="Patient Record Summarizer")
store = None

def get_store():
    global store
    if store is None:
        store = DocumentStore()
    return store

class SearchRequest(BaseModel):
    patientId: str
    question: str
    top_k: Optional[int] = 5

class SourceItem(BaseModel):
    doc_id: Optional[str]
    chunk_id: Optional[str]
    score: float
    excerpt: str

class SearchResponse(BaseModel):
    answer: str
    sources: list
    debug: dict

@app.on_event("startup")
def startup():
    try:
        get_store().ensure_indexes()
    except Exception:
        # allow startup to continue even if index creation fails in some environments
        pass

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not req.patientId or not req.question:
        raise HTTPException(status_code=400, detail="patientId and question are required")
    # compute embedding
    q_emb = get_embedding(req.question)
    retrieved = get_store().query_by_patient_and_rerank(req.patientId, q_emb, top_k=req.top_k or 5)
    answer = summarize(req.question, retrieved)
    return {"answer": answer, "sources": retrieved, "debug": {"retrieved_count": len(retrieved)}}
