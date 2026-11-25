import os
import math
import numpy as np
from typing import List, Dict, Any
from pymongo import MongoClient
from dotenv import load_dotenv

# Try to import LangChain/OpenAI; make them optional for runtime safety
try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

load_dotenv()

# Simple singleton MongoClient
_client = None

def get_mongo(uri: str) -> MongoClient:
    global _client
    if _client is None:
        # follow driver best-practices: single MongoClient per process
        _client = MongoClient(uri, retryWrites=False)
    return _client


class HybridSearcher:
    def __init__(self, documentdb_uri: str, db_name: str = "sample_retail_04"):
        self.client = get_mongo(documentdb_uri)
        self.db = self.client[db_name]
        self.col = self.db["products"]
        # embedding config
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dims = int(os.getenv("EMBEDDING_DIMS", "1536"))
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key and LANGCHAIN_AVAILABLE:
            self.emb = OpenAIEmbeddings(model=self.embedding_model, openai_api_key=self.openai_key)
            self.rewriter = ChatOpenAI(openai_api_key=self.openai_key, temperature=0.0)
        else:
            self.emb = None
            self.rewriter = None

    def rewrite_query(self, raw: str) -> str:
        """Rewrite the user's raw query into a clearer search intent.
        If LangChain/OpenAI is configured it will call the LLM; otherwise use a simple heuristic.
        """
        if self.rewriter:
            prompt = (
                "Rewrite the following user search into a concise search intent suitable for product search. "
                "Keep it short, focus on product attributes, colors, sizes, and styles.\n\nUser: {q}\n\nIntent:"
            )
            # simple direct call to the LLM
            resp = self.rewriter.generate([{"text": prompt.format(q=raw)}])
            # The langchain ChatOpenAI generate API returns complex objects; simplify
            try:
                return resp.generations[0][0].text.strip()
            except Exception:
                pass
        # fallback heuristic
        q = raw.strip()
        q = q.replace("/", " ")
        q = q.replace("\\", " ")
        # remove filler words naive
        fillers = ["please", "show", "find", "list", "i need", "i'm looking for", "looking for"]
        lq = q.lower()
        for f in fillers:
            if lq.startswith(f):
                q = q[len(f):].strip()
                break
        return q

    def embed(self, text: str) -> List[float]:
        if self.emb:
            vec = self.emb.embed_query(text)
            # normalize for cosine
            arr = np.array(vec, dtype=float)
            norm = np.linalg.norm(arr)
            if norm == 0:
                return vec
            return (arr / norm).tolist()
        raise RuntimeError("Embeddings not configured; set OPENAI_API_KEY to enable embeddings")

    def _bm25_search(self, intent: str, k: int = 10) -> List[Dict[str, Any]]:
        # Attempt a $search BM25 query via aggregation; fall back to regex find if not available
        try:
            pipeline = [
                {"$search": {"index": "default-search-index", "text": {"query": intent, "path": ["title", "description"]}}},
                {"$project": {"title": 1, "description": 1, "score": {"$meta": "searchScore"}}},
                {"$limit": k},
            ]
            docs = list(self.col.aggregate(pipeline))
            results = [{"_id": d.get("_id"), "title": d.get("title"), "description": d.get("description"), "score": d.get("score", 0)} for d in docs]
            return results
        except Exception:
            # fallback to text regex search
            cursor = self.col.find({"$or": [{"title": {"$regex": intent, "$options": "i"}}, {"description": {"$regex": intent, "$options": "i"}}]}, {"title": 1, "description": 1}).limit(k)
            results = []
            rank = 1
            for d in cursor:
                results.append({"_id": d.get("_id"), "title": d.get("title"), "description": d.get("description"), "score": 1.0 / rank})
                rank += 1
            return results

    def _vector_search(self, query_vec: List[float], k: int = 10) -> List[Dict[str, Any]]:
        # Attempt a vector $search via cosmosSearch; fall back to linear scan cosine computation
        try:
            pipeline = [
                {"$search": {"index": "default-vector-index", "cosmosSearch": {"knn": {"vector": query_vec, "path": "embedding", "k": k}}}},
                {"$project": {"title": 1, "description": 1, "score": {"$meta": "searchScore"}}},
                {"$limit": k},
            ]
            docs = list(self.col.aggregate(pipeline))
            results = [{"_id": d.get("_id"), "title": d.get("title"), "description": d.get("description"), "score": d.get("score", 0)} for d in docs]
            return results
        except Exception:
            # fallback: fetch candidates and compute cosine similarity in-app
            candidates = list(self.col.find({}, {"title": 1, "description": 1, "embedding": 1}).limit(1000))
            q = np.array(query_vec, dtype=float)
            out = []
            for d in candidates:
                emb = d.get("embedding")
                if not emb:
                    continue
                v = np.array(emb, dtype=float)
                denom = (np.linalg.norm(q) * np.linalg.norm(v))
                sim = float(np.dot(q, v) / denom) if denom != 0 else 0.0
                out.append({"_id": d.get("_id"), "title": d.get("title"), "description": d.get("description"), "score": sim})
            out.sort(key=lambda x: x["score"], reverse=True)
            return out[:k]

    def rrf_fusion(self, bm25: List[Dict[str, Any]], vector: List[Dict[str, Any]], top_n: int = 5, k_const: int = 60) -> List[Dict[str, Any]]:
        # Reciprocal Rank Fusion (RRF)
        scores = {}
        for rank, doc in enumerate(bm25, start=1):
            did = str(doc["_id"])
            scores.setdefault(did, {"doc": doc, "rrf": 0.0})
            scores[did]["rrf"] += 1.0 / (k_const + rank)
        for rank, doc in enumerate(vector, start=1):
            did = str(doc["_id"])
            scores.setdefault(did, {"doc": doc, "rrf": 0.0})
            scores[did]["rrf"] += 1.0 / (k_const + rank)
        # convert to list
        merged = []
        for did, val in scores.items():
            entry = val["doc"].copy()
            entry["rrf_score"] = val["rrf"]
            merged.append(entry)
        merged.sort(key=lambda x: x["rrf_score"], reverse=True)
        return merged[:top_n]

    def search(self, raw_query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        intent = self.rewrite_query(raw_query)
        try:
            vec = self.embed(intent) if self.emb else None
        except Exception:
            vec = None
        bm25_res = self._bm25_search(intent, k=top_n * 3)
        vector_res = self._vector_search(vec, k=top_n * 3) if vec is not None else []
        fused = self.rrf_fusion(bm25_res, vector_res, top_n=top_n)
        return fused
