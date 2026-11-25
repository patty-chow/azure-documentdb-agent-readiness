import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from db import get_collection
import openai

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # allow service to start but will fail at runtime if embedding is attempted
    print("Warning: OPENAI_API_KEY not set; embedding calls will fail until provided.")
openai.api_key = OPENAI_API_KEY

EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.environ.get("EMBED_DIMENSIONS", "1536"))

app = FastAPI(title="Formulary Semantic Search")

class QueryRequest(BaseModel):
    query: str

@app.post("/formulary-search")
async def formulary_search(req: QueryRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="'query' is required")
    # embed the query
    try:
        resp = openai.Embedding.create(model=EMBED_MODEL, input=req.query)
        qvec = resp['data'][0]['embedding']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failure: {e}")

    coll = get_collection()
    # Build aggregation using cosmosSearch vector knn
    pipeline = [
        {"$search": {"cosmosSearch": {"path": "embedding", "vector": qvec, "k": 10, "lSearch": 100}}},
        {"$project": {"name": 1, "indications": 1, "contraindications":1, "dosing":1, "score": {"$meta": "searchScore"}}},
        {"$limit": 10}
    ]

    try:
        docs = list(coll.aggregate(pipeline))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search query failed: {e}")

    return {"results": docs}
