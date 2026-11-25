import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai
from src.db import get_db

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", 1536))
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def embed_text(text: str) -> List[float]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings in this sample")
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    vec = resp["data"][0]["embedding"]
    if len(vec) != EMBEDDING_DIMS:
        print("Warning: embedding size", len(vec), "does not match EMBEDDING_DIMS", EMBEDDING_DIMS)
    return vec


def search_correspondent(correspondent_id: str, k: int = 5) -> Dict[str, Any]:
    db = get_db()
    corr = db["correspondents"].find_one({"_id": correspondent_id})
    if not corr:
        raise ValueError("Correspondent not found: " + correspondent_id)

    # Ensure the correspondent has an embedding; create if missing
    if "embedding" not in corr:
        profile_text = f"{corr.get('name','')}. Country: {corr.get('country','')}. Notes: {corr.get('notes','')}."
        emb = embed_text(profile_text)
        db["correspondents"].update_one({"_id": correspondent_id}, {"$set": {"embedding": emb}})
        corr["embedding"] = emb

    vector = corr["embedding"]

    sanctions_matches = []
    adverse_matches = []

    # Attempt vector search on sanctions
    sanctions_pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": vector,
                    "path": "embedding",
                    "k": k
                }
            }
        },
        {"$limit": k}
    ]

    try:
        sanctions_matches = list(db["sanctions"].aggregate(sanctions_pipeline))
    except Exception as e:
        print("Sanctions vector search failed or not available, falling back to metadata/text match:", e)
        # metadata fallback: exact entity_name match
        sanctions_matches = list(db["sanctions"].find({"entity_name": corr.get('name','')}).limit(k))

    # Attempt vector search on adverse_media
    adverse_pipeline = [
        {
            "$search": {
                "cosmosSearch": {
                    "vector": vector,
                    "path": "embedding",
                    "k": k
                }
            }
        },
        {"$limit": k}
    ]

    try:
        adverse_matches = list(db["adverse_media"].aggregate(adverse_pipeline))
    except Exception as e:
        print("Adverse media vector search failed or not available, falling back to headline substring match:", e)
        name = corr.get('name','')
        adverse_matches = list(db["adverse_media"].find({"headline": {"$regex": name, "$options": "i"}}).limit(k))

    # Simple scoring: count matches and weight by a simulated score field if present
    score = 0.0
    matched = []
    for m in sanctions_matches:
        matched.append({"type": "sanction", "id": m.get("_id"), "title": m.get("title",""), "excerpts": m})
        score += 0.6
    for m in adverse_matches:
        matched.append({"type": "adverse_media", "id": m.get("_id"), "headline": m.get("headline",""), "excerpts": m})
        score += 0.4

    # Normalize score to 0-100
    risk_score = min(100, int(score * 25))

    # Compose plain-language narrative using the LLM
    narrative = "No narrative available (LLM disabled)"
    if OPENAI_API_KEY:
        prompt = (
            f"You are a compliance analyst. Given the correspondent profile:\n{corr}\n\n"
            f"And the following matches:\n{matched}\n\n"
            "Write a concise plain-language risk narrative (3-5 sentences) and summarize why this correspondent received the computed risk score."
        )
        try:
            resp = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2,
            )
            narrative = resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            narrative = f"LLM call failed: {e}"

    return {
        "correspondent_id": correspondent_id,
        "risk_score": risk_score,
        "matched": matched,
        "narrative": narrative,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent <correspondent_id>")
        sys.exit(1)
    res = search_correspondent(sys.argv[1])
    print(res)
