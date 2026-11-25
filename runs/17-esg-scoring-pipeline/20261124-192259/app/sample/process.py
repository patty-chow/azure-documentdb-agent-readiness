"""Process documents: generate E/S/G scores + rationales and embeddings, then update the documents.

Run as: python -m sample.process
"""
import os
from pymongo import UpdateOne
from .db import get_db
from .config import COLLECTION_NAME, FALLBACK_MODE, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, OPENAI_LLM_MODEL, EMBEDDING_DIMS
from .utils import deterministic_scores_from_text, deterministic_embedding, normalize_embedding

try:
    from langchain import OpenAI
    from langchain.embeddings import OpenAIEmbeddings
except Exception:
    OpenAI = None
    OpenAIEmbeddings = None

COLLATE_BATCH = 10


def call_llm_scores(text):
    """Return scores [E,S,G] and rationales [rE, rS, rG]. Uses OpenAI via LangChain if configured; otherwise deterministic fallback."""
    if not FALLBACK_MODE and OPENAI_API_KEY and OpenAI is not None:
        # Using simple prompt engineering via LangChain OpenAI wrapper
        client = OpenAI(model_name=OPENAI_LLM_MODEL)
        prompt = f"Score the following company ESG description on a 1-10 scale for Environmental (E), Social (S), and Governance (G). Respond in JSON: {{\"E\": int, \"S\": int, \"G\": int, \"rationale_E\": str, \"rationale_S\": str, \"rationale_G\": str}}\n\nText: '''{text}'''"
        resp = client.predict(prompt)
        # Post-process: naive parsing attempt
        import json
        try:
            parsed = json.loads(resp)
            return [parsed.get("E"), parsed.get("S"), parsed.get("G")], [parsed.get("rationale_E"), parsed.get("rationale_S"), parsed.get("rationale_G")]
        except Exception:
            # fallback to deterministic
            pass
    # Fallback deterministic
    scores, rationales = deterministic_scores_from_text(text)
    return scores, rationales


def get_embedding(text):
    if not FALLBACK_MODE and OPENAI_API_KEY and OpenAIEmbeddings is not None:
        emb = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        vec = emb.embed_query(text)
        return normalize_embedding(vec)
    return deterministic_embedding(text, dims=EMBEDDING_DIMS)


def process_all():
    db = get_db()
    col = db[COLLECTION_NAME]
    cursor = col.find({"score_E": {"$exists": False}})
    ops = []
    count = 0
    for doc in cursor:
        text = doc.get("raw_esg_text", "")
        scores, rationales = call_llm_scores(text)
        emb = get_embedding(" \n".join(rationales))
        update = {
            "$set": {
                "score_E": int(scores[0]) if scores and scores[0] is not None else None,
                "score_S": int(scores[1]) if scores and scores[1] is not None else None,
                "score_G": int(scores[2]) if scores and scores[2] is not None else None,
                "rationale_E": rationales[0],
                "rationale_S": rationales[1],
                "rationale_G": rationales[2],
                "rationale_embedding": emb,
            }
        }
        ops.append(UpdateOne({"_id": doc["_id"]}, update))
        count += 1
        if len(ops) >= COLLATE_BATCH:
            res = col.bulk_write(ops)
            print(f"Wrote batch, matched={res.matched_count} modified={res.modified_count}")
            ops = []
    if ops:
        res = col.bulk_write(ops)
        print(f"Wrote final batch, matched={res.matched_count} modified={res.modified_count}")
    print(f"Processed {count} documents")


if __name__ == "__main__":
    process_all()
