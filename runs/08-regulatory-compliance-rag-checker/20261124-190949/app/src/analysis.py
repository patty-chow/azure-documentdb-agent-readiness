"""Simple analysis CLI that retrieves relevant regulatory clauses for a policy excerpt and emits a compliance gap report.
This demo uses local cosine similarity over stored embeddings (if available)."""
import os
import argparse
import math
from dotenv import load_dotenv
from src.db import get_db

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3")


def cosine_sim(a, b):
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return -1.0
    return dot / (na * nb)


def embed_text(text):
    if not OPENAI_API_KEY:
        return None
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        res = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=[text])
        return res["data"][0]["embedding"]
    except Exception as e:
        print("Embedding failed:", e)
        return None


def analyze_text(text, top_k=3):
    db = get_db()
    regs = list(db.regulations.find({}))
    policies = list(db.policies.find({}))

    query_emb = embed_text(text)
    results = []
    if query_emb:
        # compare to regs embeddings
        for r in regs:
            emb = r.get("embedding")
            if emb:
                sim = cosine_sim(query_emb, emb)
            else:
                sim = 0.0
            results.append((sim, r))
        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:top_k]
    else:
        # fallback keyword match: count common words
        qset = set(text.lower().split())
        scored = []
        for r in regs:
            rset = set(r.get("text","").lower().split())
            sim = len(qset & rset)
            scored.append((sim, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

    # Build a simple compliance-gap heuristic: if top matched clause similarity >= 0.8 -> compliant
    verdict = "unknown"
    gaps = []
    if query_emb:
        best_sim = top[0][0]
        if best_sim >= 0.85:
            verdict = "compliant"
        elif best_sim >= 0.5:
            verdict = "partial"
        else:
            verdict = "non-compliant"
        for sim, r in top:
            gaps.append({"reg_id": r["_id"], "sim": sim, "title": r.get("title")})
    else:
        # heuristic for keyword
        best_score = top[0][0]
        if best_score >= 3:
            verdict = "compliant"
        elif best_score >= 1:
            verdict = "partial"
        else:
            verdict = "non-compliant"
        for score, r in top:
            gaps.append({"reg_id": r["_id"], "score": score, "title": r.get("title")})

    report = {"verdict": verdict, "matches": gaps, "query": text}
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True, help="Policy excerpt to analyze")
    args = p.parse_args()
    rpt = analyze_text(args.text)
    import json
    print(json.dumps(rpt, indent=2))
