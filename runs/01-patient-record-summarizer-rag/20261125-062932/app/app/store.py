import math
from typing import List, Dict, Any
from .db import get_collection

# Simple document store abstraction that persists chunks with embeddings

class DocumentStore:
    def __init__(self, collection=None):
        self.collection = collection or get_collection()

    def ensure_indexes(self):
        # Ensure an index on patientId for efficient filtering
        self.collection.create_index([("patientId", 1)])

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        # Insert many chunks; upsert by _id if provided
        for c in chunks:
            if "_id" in c:
                self.collection.replace_one({"_id": c["_id"]}, c, upsert=True)
            else:
                self.collection.insert_one(c)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        # compute cosine similarity between two lists
        if not a or not b:
            return 0.0
        dot = sum(x*y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x*x for x in a))
        norm_b = math.sqrt(sum(y*y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def query_by_patient_and_rerank(self, patient_id: str, query_embedding: List[float], top_k: int = 5):
        # Fetch candidate chunks for patient and compute cosine similarity in application
        cursor = self.collection.find({"patientId": patient_id}, {"text": 1, "embedding": 1, "source_doc_id":1, "chunk_id":1})
        results = []
        for doc in cursor:
            emb = doc.get("embedding")
            if not emb:
                continue
            score = float(self._cosine_similarity(query_embedding, emb))
            results.append({"doc": doc, "score": score})
        # sort descending by score
        results.sort(key=lambda r: r["score"], reverse=True)
        top = results[:top_k]
        # format
        formatted = []
        for r in top:
            d = r["doc"]
            formatted.append({
                "doc_id": d.get("source_doc_id"),
                "chunk_id": d.get("chunk_id"),
                "score": r["score"],
                "excerpt": (d.get("text") or "")[:300]
            })
        return formatted
