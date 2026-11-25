import os
import math
from typing import Dict, Any, List, Optional

import numpy as np
from .db import get_collection
from .embeddings import embed_text, embed_texts

# LLM optional: use LangChain chat model if OPENAI_API_KEY is present
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _search_collection_by_embedding(collection_name: str, query_emb: List[float], top_k: int = 5):
    coll = get_collection(collection_name)
    # fetch documents that have embeddings
    docs = list(coll.find({"embedding": {"$exists": True}}, {"embedding": 1, "_id": 1, "title": 1, "entry_text": 1, "snippet": 1, "source": 1, "date": 1}))
    results = []
    for d in docs:
        emb = d.get("embedding")
        if not emb:
            continue
        score = cosine_similarity(query_emb, emb)
        results.append({"doc": d, "score": score})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def compute_risk_score(matches: List[Dict[str, Any]]) -> int:
    """Simple heuristic: map max similarity to 0-100 and boost by number of close matches."""
    if not matches:
        return 0
    max_sim = max(m["score"] for m in matches)
    num_close = sum(1 for m in matches if m["score"] > 0.75)
    score = int(min(100, max_sim * 100 + num_close * 10))
    return score


def generate_narrative(profile_text: str, matches: List[Dict[str, Any]], risk_score: int) -> str:
    if LLM_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        chat = ChatOpenAI(model=LLM_MODEL, temperature=0.2)
        matched_summaries = []
        for m in matches[:5]:
            doc = m["doc"]
            text = doc.get("entry_text") or doc.get("snippet") or doc.get("title") or ""
            matched_summaries.append(f"- {text} (score={m['score']:.3f})")
        prompt = (
            f"You are a compliance analyst. Given the correspondent profile:\n{profile_text}\n\nMatches:\n{chr(10).join(matched_summaries)}\n\nProvide a concise plain-language risk narrative and recommended next steps. Include the overall risk score {risk_score}.")
        resp = chat([HumanMessage(content=prompt)])
        return resp[0].content.strip()
    # fallback deterministic narrative
    lines = [f"Risk score: {risk_score}."]
    if not matches:
        lines.append("No relevant sanctions or adverse media matches were found.")
    else:
        lines.append("Top matches:")
        for m in matches[:5]:
            doc = m["doc"]
            title = doc.get("title") or doc.get("_id")
            lines.append(f"- {title}: score={m['score']:.3f}")
        if risk_score >= 70:
            lines.append("Summary: High risk due to strong semantic matches; consider enhanced due diligence and transaction monitoring.")
        elif risk_score >= 40:
            lines.append("Summary: Medium risk; review recent transactions and counterparties.")
        else:
            lines.append("Summary: Low risk based on available data.")
    return "\n".join(lines)


def synthetic_embedding(text: str, dim: int = 1536):
    import hashlib
    h = hashlib.sha256((text or "").encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
    v = rng.random(dim).astype(float)
    v = v / (np.linalg.norm(v) + 1e-12)
    return v.tolist()


def review_correspondent(correspondent_id: Optional[str] = None, profile_text: Optional[str] = None) -> Dict[str, Any]:
    if not correspondent_id and not profile_text:
        raise ValueError("Either correspondent_id or profile_text must be provided")
    if correspondent_id:
        coll = get_collection("correspondents")
        doc = coll.find_one({"_id": correspondent_id})
        if not doc:
            raise ValueError(f"Correspondent with id {correspondent_id} not found")
        profile_text = doc.get("profile_text") or ""

    # compute embedding for the profile; fallback to deterministic synthetic if API not available
    try:
        query_emb = embed_text(profile_text)
    except Exception:
        query_emb = synthetic_embedding(profile_text)

    # search sanctions and adverse media client-side
    sanctions_matches = _search_collection_by_embedding("sanctions", query_emb, top_k=5)
    adverse_matches = _search_collection_by_embedding("adverse_media", query_emb, top_k=5)

    all_matches = sanctions_matches + adverse_matches
    all_matches.sort(key=lambda r: r["score"], reverse=True)

    risk_score = compute_risk_score(all_matches)
    narrative = generate_narrative(profile_text, all_matches, risk_score)

    # format matches for output
    formatted = []
    for m in all_matches[:10]:
        doc = m["doc"]
        formatted.append({
            "id": str(doc.get("_id")),
            "title": doc.get("title") or doc.get("snippet") or doc.get("entry_text"),
            "score": float(m["score"]),
            "source": doc.get("source"),
            "date": doc.get("date"),
        })

    return {
        "risk_score": int(risk_score),
        "matches": formatted,
        "risk_narrative": narrative,
    }
