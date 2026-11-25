"""Agent that generates embeddings and searches stored fraud patterns.
Uses LangChain OpenAIEmbeddings when OPENAI_API_KEY is present; otherwise uses deterministic mock embeddings.
Performs client-side cosine similarity if server-side vector search is unavailable.
"""
import os
import math
from typing import List, Dict, Any
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DOC_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = "sample_fintech_01"
COLLECTION = "fraud_patterns"

USE_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))

if USE_OPENAI:
    try:
        from langchain.embeddings import OpenAIEmbeddings
        _emb_model = OpenAIEmbeddings()
    except Exception as e:
        print("Failed to load LangChain OpenAIEmbeddings, falling back to mock. Error:", e)
        USE_OPENAI = False


def mock_embedding(text: str, dim: int = 128):
    h = abs(hash(text))
    rnd = __import__("random").Random(h)
    return [rnd.random() for _ in range(dim)]


def get_embedding(text: str) -> List[float]:
    if USE_OPENAI:
        emb = _emb_model.embed_query(text)
        return emb
    else:
        return mock_embedding(text)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class FraudAgent:
    def __init__(self, uri: str = None):
        self.uri = uri or DOC_URI
        self.client = MongoClient(self.uri)
        self.db = self.client[DB_NAME]
        self.col = self.db[COLLECTION]

    def search_similar(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Try server-side vector search if available; otherwise fetch candidates and do client-side cosine similarity."""
        # Attempt a server-side $search with vector semantics — not all clusters support this operator or syntax.
        try:
            pipeline = [
                {"$addFields": {"_score": {"$meta": "searchScore"}}},
                {"$limit": 100}
            ]
            # This will usually not run on vanilla servers; it's a best-effort placeholder.
            cursor = list(self.col.aggregate(pipeline))
            if cursor:
                # If this returns results, compute similarity if embedding fields exist
                matches = []
                for doc in cursor:
                    if "embedding" in doc:
                        sim = cosine_similarity(embedding, doc["embedding"])
                        matches.append({"doc": doc, "score": float(sim)})
                matches.sort(key=lambda x: x["score"], reverse=True)
                return matches[:top_k]
        except Exception:
            # server-side vector search not available or query failed; fall back
            pass

        # Client-side fallback: fetch all pattern docs and compute cosine similarity
        docs = list(self.col.find({}, {"_id": 0, "pattern_id": 1, "description": 1, "example_transactions": 1, "embedding": 1, "metadata": 1}))
        scored = []
        for d in docs:
            emb = d.get("embedding")
            if not emb:
                continue
            sim = cosine_similarity(embedding, emb)
            scored.append({"doc": d, "score": float(sim)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def score_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        # Create a simple textual representation to embed
        text = f"tx:{transaction.get('tx_id','')}; amt:{transaction.get('amount',0)}; desc:{transaction.get('description','')};"
        emb = get_embedding(text)
        matches = self.search_similar(emb, top_k=5)
        # Compute a simple risk score: weighted sum of matched severities * similarity
        score = 0.0
        explanation_items = []
        for m in matches:
            doc = m["doc"]
            sim = m["score"]
            severity = float(doc.get("metadata", {}).get("severity", 1))
            contribution = sim * severity
            score += contribution
            explanation_items.append({"pattern_id": doc.get("pattern_id"), "similarity": sim, "severity": severity, "description": doc.get("description")})
        # normalize score to 0-100 (heuristic)
        normalized = min(100.0, score * 20.0)
        explanation = "Matches found: " + "; ".join([f"{it['pattern_id']} (sim={it['similarity']:.2f}, sev={it['severity']})" for it in explanation_items])
        return {"risk_score": normalized, "explanation": explanation, "matches": explanation_items}
