import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.db import get_sanctions_collection
import openai
from src.utils import combine_scores

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
VECTOR_WEIGHT = float(os.environ.get("VECTOR_WEIGHT", "0.7"))
REGEX_WEIGHT = float(os.environ.get("REGEX_WEIGHT", "0.3"))
TOP_K = int(os.environ.get("TOP_K", "10"))

app = FastAPI(title="Sanctions Screening Agent")

class ScreenRequest(BaseModel):
    name: str
    country: str = None

class Candidate(BaseModel):
    id: str
    name: str
    match_confidence: float
    recommended_action: str
    reasons: Dict[str, Any]

class ScreenResponse(BaseModel):
    query: Dict[str, Any]
    candidates: List[Candidate]


@app.post("/screen", response_model=ScreenResponse)
def screen(req: ScreenRequest):
    if not req.name:
        raise HTTPException(status_code=400, detail="name is required")
    coll = get_sanctions_collection()

    # compute embedding for the query
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    openai.api_key = api_key
    emb_resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=req.name)
    q_emb = emb_resp["data"][0]["embedding"]

    # vector search via $search + cosmosSearch
    pipeline = [
        {"$search": {"cosmosSearch": {"vector": q_emb, "path": "embedding", "k": TOP_K}, "returnStoredSource": True}},
        {"$project": {"score": {"$meta": "searchScore"}, "document": "$$ROOT"}},
    ]
    vec_results = list(coll.aggregate(pipeline))

    # build candidate dict
    candidates = {}
    for r in vec_results:
        score = r.get("score", 0.0)
        doc = r.get("document", {})
        doc_id = doc.get("_id")
        candidates[doc_id] = {
            "id": doc_id,
            "name": doc.get("name"),
            "vector_score": float(score),
            "regex_score": 0.0,
        }

    # regex fuzzy matching (simple contains, case-insensitive)
    pattern = re.compile(re.escape(req.name), re.IGNORECASE)
    # search name and alt_names fields
    regex_cursor = coll.find({"$or": [{"name": {"$regex": pattern.pattern, "$options": "i"}}, {"alt_names": {"$elemMatch": {"$regex": pattern.pattern, "$options": "i"}}}]}, projection={"name": 1})
    for d in regex_cursor:
        doc_id = d.get("_id")
        if doc_id in candidates:
            candidates[doc_id]["regex_score"] = 1.0
        else:
            candidates[doc_id] = {
                "id": doc_id,
                "name": d.get("name"),
                "vector_score": 0.0,
                "regex_score": 1.0,
            }

    # combine and rank
    merged = []
    for c in candidates.values():
        combined = combine_scores(c.get("vector_score", 0.0), c.get("regex_score", 0.0), VECTOR_WEIGHT, REGEX_WEIGHT)
        if combined >= float(os.environ.get("HIGH_CONFIDENCE", "0.8")):
            action = "Review immediately - high confidence match"
        elif combined >= float(os.environ.get("MEDIUM_CONFIDENCE", "0.5")):
            action = "Manual review - possible match"
        else:
            action = "No action needed"
        merged.append(Candidate(id=c["id"], name=c["name"], match_confidence=combined, recommended_action=action, reasons={"vector_score": c.get("vector_score"), "regex_score": c.get("regex_score")}))

    merged_sorted = sorted(merged, key=lambda x: x.match_confidence, reverse=True)
    return ScreenResponse(query={"name": req.name, "country": req.country}, candidates=merged_sorted)
