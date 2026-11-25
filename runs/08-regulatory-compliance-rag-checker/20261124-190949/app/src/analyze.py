"""CLI analyze: compute embedding for the input excerpt and return a simple
compliance gap report by comparing the excerpt against regulations.

Usage:
  python -m src.analyze "policy excerpt text..."
"""
import os
import sys
import numpy as np
from dotenv import load_dotenv
from src.db import get_db

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))
USE_SERVER_SEARCH = os.getenv("USE_SERVER_SEARCH", "false").lower() == "true"

if OPENAI_API_KEY:
    import openai
    openai.api_key = OPENAI_API_KEY


def compute_embedding(text: str):
    if not OPENAI_API_KEY:
        return None
    resp = openai.Embedding.create(input=text, model="text-embedding-3")
    return resp["data"][0]["embedding"]


def cos_sim(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def client_side_search(query_emb, top_k=3):
    db = get_db()
    regs = list(db.regulations.find({}))
    scored = []
    for r in regs:
        emb = r.get("embedding")
        if not emb:
            continue
        score = cos_sim(query_emb, emb)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored[:top_k]]


def analyze_text(text):
    emb = compute_embedding(text) if OPENAI_API_KEY else None
    results = []
    if emb and USE_SERVER_SEARCH:
        # Try server-side $search with cosmosSearch
        db = get_db()
        pipeline = [
            {"$search": {"cosmosSearch": {"vector": {"path": "embedding", "queryVector": emb, "k": 5}}}},
            {"$limit": 5},
        ]
        try:
            docs = list(db.regulations.aggregate(pipeline))
            results = docs
        except Exception as e:
            print("Server-side $search failed, falling back to client-side search:", e)
            results = client_side_search(emb)
    elif emb:
        results = client_side_search(emb)
    else:
        # No embedding available: fallback to simple text match on keyword intersection
        db = get_db()
        tokens = [t.lower() for t in text.split() if len(t) > 3]
        cursor = db.regulations.find({"text": {"$regex": "|".join(tokens), "$options": "i"}}).limit(5)
        results = list(cursor)

    # Build a small compliance report
    report = {
        "verdict": "partial",
        "matches": [],
    }
    if not results:
        report["verdict"] = "no_matches"
        report["explanation"] = "No relevant regulatory clauses found for the excerpt."
        return report

    # Very naive heuristics for compliance gaps
    for r in results:
        rule = {
            "reg_id": r.get("_id"),
            "title": r.get("title"),
            "text": r.get("text"),
        }
        # If excerpt contains words from the regulation text, we mark as aligned
        excerpt = text.lower()
        overlap = sum(1 for w in r.get("text", "").lower().split() if w in excerpt)
        rule["overlap_tokens"] = overlap
        report["matches"].append(rule)

    # Simple verdict rules
    if all(m["overlap_tokens"] > 0 for m in report["matches"]):
        report["verdict"] = "compliant_or_aligned"
    elif any(m["overlap_tokens"] > 0 for m in report["matches"]):
        report["verdict"] = "partial"
    else:
        report["verdict"] = "non_compliant_or_gap"

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.analyze \"policy excerpt\"")
        sys.exit(1)
    text = sys.argv[1]
    r = analyze_text(text)
    import json
    print(json.dumps(r, indent=2))
