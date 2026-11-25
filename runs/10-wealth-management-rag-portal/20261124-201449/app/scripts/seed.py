"""Seed script for the sample data.
Creates collections, the vector index, and inserts sample research documents and portfolios.

If OPENAI_API_KEY is present, it will call OpenAI embeddings; otherwise it will generate synthetic embeddings.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid
import time
from typing import List, Dict
from dotenv import load_dotenv
from src import db

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    _openai_client = None


def get_embedding(text: str) -> List[float]:
    if _openai_client:
        resp = _openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        return resp.data[0].embedding
    # fallback
    return db.generate_synthetic_embedding(text)


def make_sample_research(n=30):
    docs = []
    for i in range(n):
        _id = f"RD-{i+1:03d}"
        title = f"Market Research Piece {_id}"
        content = (
            f"Research content for {_id}. \nThis report discusses interest rates, credit spreads, and sector positioning."
            + " More detailed commentary and scenario analysis."
        )
        embedding = get_embedding(title + "\n" + content)
        docs.append({"_id": _id, "title": title, "content": content, "metadata": {"sector": "Fixed Income"}, "embedding": embedding})
    return docs


def make_sample_portfolios():
    portfolios = []
    portfolios.append({
        "client_id": "C123",
        "positions": [
            {"ticker": "US10Y", "type": "bond", "notional": 1000000, "duration": 8.5},
            {"ticker": "ACME-Corp", "type": "equity", "notional": 250000},
        ],
        "metadata": {"client_segment": "HNW", "risk_tolerance": "moderate"},
    })
    portfolios.append({
        "client_id": "C456",
        "positions": [
            {"ticker": "US2Y", "type": "bond", "notional": 500000, "duration": 2.0},
            {"ticker": "BigBank", "type": "equity", "notional": 150000},
        ],
        "metadata": {"client_segment": "UHNW", "risk_tolerance": "conservative"},
    })
    return portfolios


if __name__ == "__main__":
    print("Ensuring collections and indexes...")
    db.ensure_collections_and_indexes()
    print("Seeding research documents...")
    docs = make_sample_research(30)
    db.upsert_research_documents(docs)
    print(f"Inserted/updated {len(docs)} research documents.")
    print("Seeding portfolios...")
    for p in make_sample_portfolios():
        db.upsert_portfolio(p)
    print("Portfolios upserted.")
    print("Done.")
