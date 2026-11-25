from typing import List, Dict
from .db import get_db
import heapq
import math

COLLECTION = "high_risk_profiles"


def ensure_vector_index(client=None, dimensions=1536):
    db = get_db()
    coll = db[COLLECTION]
    try:
        cmd = {
            "createIndexes": COLLECTION,
            "indexes": [
                {
                    "key": {"embedding": "cosmosSearch"},
                    "name": "embedding_cosmos_search",
                    "cosmosSearchOptions": {
                        "kind": "vector-diskann",
                        "similarity": "COS",
                        "dimensions": dimensions,
                        "maxDegree": 32,
                        "lBuild": 50
                    }
                }
            ]
        }
        res = db.command(cmd)
        return res
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _cosine(a, b):
    # assume pre-normalized vectors; otherwise compute normalization
    if a is None or b is None:
        return -1.0
    # dot product
    return sum(x * y for x, y in zip(a, b))


def retrieve_similar(embedding: List[float], k: int = 5) -> List[Dict]:
    db = get_db()
    coll = db[COLLECTION]
    pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": {
                        "path": "embedding",
                        "k": k,
                        "value": embedding,
                        "similarity": "COS"
                    }
                }
            }
        },
        {
            "$project": {
                "patient_id": 1,
                "features": 1,
                "risk_label": 1,
                "recommended_interventions": 1,
                "score": {"$meta": "searchScore"}
            }
        }
    ]
    try:
        results = list(coll.aggregate(pipeline))
        return results
    except Exception:
        # Fallback: client-side linear scan with cosine similarity
        docs = list(coll.find({"embedding": {"$exists": True}}, {"embedding": 1, "patient_id": 1, "features": 1, "risk_label": 1, "recommended_interventions": 1}))
        scored = []
        for d in docs:
            emb = d.get("embedding")
            if not isinstance(emb, list):
                continue
            score = _cosine(embedding, emb)
            scored.append((score, d))
        top = heapq.nlargest(k, scored, key=lambda x: x[0])
        out = []
        for score, d in top:
            d_out = {
                "patient_id": d.get("patient_id"),
                "features": d.get("features"),
                "risk_label": d.get("risk_label"),
                "recommended_interventions": d.get("recommended_interventions"),
                "score": float(score)
            }
            out.append(d_out)
        return out
