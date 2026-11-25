from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import numpy as np

load_dotenv()

DOCUMENTDB_URI = os.environ.get('DOCUMENTDB_URI')
DB_NAME = os.environ.get('DB_NAME', 'sample_banking_10')

if not DOCUMENTDB_URI:
    raise RuntimeError('DOCUMENTDB_URI must be set in environment or in a .env file')

client = MongoClient(DOCUMENTDB_URI, retryWrites=False)
db = client[DB_NAME]

app = FastAPI(title='Wealth Management RAG (DocumentDB)')

class QueryRequest(BaseModel):
    client_id: str
    question: str
    top_k: int = 5

@app.post('/query')
def query(req: QueryRequest):
    # Fetch portfolio
    portfolio = db.portfolios.find_one({'client_id': req.client_id})
    if not portfolio:
        raise HTTPException(status_code=404, detail='Portfolio not found')

    # Simple vector search: use precomputed embeddings stored on docs and cosine similarity
    # This is a fallback retrieval if a native $search vector index is not present.
    # Load top_k docs by cosine similarity to a synthetic 'query embedding' (not a real embedding)
    # For demo, we craft a query embedding as the mean of portfolio position tickers hashed.
    portfolio_text = ' '.join([p.get('ticker','') for p in portfolio.get('positions',[])])
    # Create a deterministic pseudo-embedding from portfolio text
    q_emb = _text_to_embedding(portfolio_text)

    # Fetch candidate docs (limit to 200) and score
    candidates = list(db.research_documents.find({}, projection={'title':1,'content':1,'embedding':1,'metadata':1}).limit(200))
    scored = []
    for doc in candidates:
        emb = doc.get('embedding')
        if not emb:
            continue
        score = _cosine_similarity(q_emb, emb)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [{'score': float(s), 'doc': d} for s,d in scored[:req.top_k]]

    # Compose a simple answer combining portfolio and top docs
    answer = _compose_answer(portfolio, top, req.question)
    return {'answer': answer, 'retrieved': top}


# Helpers

def _text_to_embedding(text, dim=1536):
    if not text:
        return [0.0]*dim
    # deterministic hash-based pseudo-embedding
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    rng = np.random.default_rng(seed=int.from_bytes(h[:8], 'big'))
    v = rng.standard_normal(dim)
    v = v / np.linalg.norm(v)
    return v.tolist()


def _cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a)*np.linalg.norm(b)))


def _compose_answer(portfolio, retrieved, question):
    # Very small template-based composer. In real app this would call a LLM with context.
    lines = []
    lines.append(f"Question: {question}")
    lines.append(f"Client: {portfolio.get('client_id')}, positions: {len(portfolio.get('positions',[]))}")
    lines.append('Top supporting research:')
    for r in retrieved:
        lines.append(f"- {r['doc'].get('title')} (score={r['score']:.3f})")
    lines.append('\nNotes: This answer is produced by a demo agent that combines portfolio context with retrieved research. For production-grade answers, configure an LLM and use the RAG pipeline with LlamaIndex.')
    return '\n'.join(lines)
