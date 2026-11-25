import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.search import HybridSearcher

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI not set; copy .env.example to .env and set it")

app = FastAPI(title="DocumentDB Hybrid Search Sample")
searcher = HybridSearcher(documentdb_uri=DOCUMENTDB_URI)

class SearchRequest(BaseModel):
    q: str
    top_n: int = 5

@app.post("/search")
async def search(req: SearchRequest):
    if not req.q:
        raise HTTPException(status_code=400, detail="query 'q' is required")
    results = searcher.search(req.q, top_n=req.top_n)
    return {"query": req.q, "results": results}
