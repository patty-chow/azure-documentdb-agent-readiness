from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from app.db import get_db
from dotenv import load_dotenv

load_dotenv()
# optional OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Provider Directory Semantic Search")

class FindRequest(BaseModel):
    query: str
    k: int = 5

class ProviderHit(BaseModel):
    name: str
    specialty: str
    languages: List[str]
    insurance: List[str]
    bio: str
    score: float

@app.post("/find-provider", response_model=List[ProviderHit])
async def find_provider(req: FindRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="query is required")

    # embed the query (use OpenAI if key present and package installed, else fallback)
    vec = None
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        resp = openai.Embedding.create(input=req.query, model=OPENAI_MODEL)
        vec = resp["data"][0]["embedding"]
    else:
        # deterministic fallback: hash-based pseudo-embedding
        import hashlib
        h = hashlib.sha256(req.query.encode('utf-8')).digest()
        # expand to 1536 dims by repeating hashed bytes
        dims = 1536
        floats = []
        for i in range(dims):
            b = h[i % len(h)]
            floats.append((b / 255.0) * 2.0 - 1.0)
        vec = floats

    db = get_db("sample_healthcare_20")
    coll = db["providers"]

    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": vec,
                    "path": "embedding",
                    "k": req.k
                },
                "returnStoredSource": True
            }
        },
        {"$project": {"score": {"$meta": "searchScore"}, "doc": "$$ROOT"}},
        {"$limit": req.k}
    ]

    docs = list(coll.aggregate(pipeline))
    results = []
    for d in docs:
        doc = d.get('doc')
        source = doc if 'name' in doc else doc.get('document', doc)
        score = d.get('score') or d.get('searchScore') or 0
        results.append(ProviderHit(
            name=source.get('name',''),
            specialty=source.get('specialty',''),
            languages=source.get('languages',[]),
            insurance=source.get('insurance',[]),
            bio=source.get('bio',''),
            score=float(score)
        ))
    return results
