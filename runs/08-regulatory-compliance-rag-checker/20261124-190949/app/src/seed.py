"""Seed a small set of synthetic regulatory clauses and internal policies.

If OPENAI_API_KEY is present the script computes embeddings and stores them in
field `embedding` (as a list of floats). Otherwise the documents are inserted
without embeddings so the rest of the sample can still run (text fallback).

Run: python src/seed.py
"""
import os
import time
from dotenv import load_dotenv
from src.db import get_db

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))

# lazy import OpenAI only if key is present
if OPENAI_API_KEY:
    import openai
    openai.api_key = OPENAI_API_KEY

REGULATIONS = [
    {
        "_id": "reg-001",
        "title": "Data Protection Act - Encryption at rest",
        "section_id": "DPA-3.1",
        "jurisdiction": "US",
        "text": "Personal data must be encrypted at rest using industry standard algorithms.",
        "schemaVersion": 1,
    },
    {
        "_id": "reg-002",
        "title": "Data Protection Act - Data in transit",
        "section_id": "DPA-3.2",
        "jurisdiction": "US",
        "text": "Personal data in transit must be protected with TLS 1.2 or higher.",
        "schemaVersion": 1,
    },
    {
        "_id": "reg-003",
        "title": "Payments Regulation - Audit Trails",
        "section_id": "PAY-7.4",
        "jurisdiction": "EU",
        "text": "Audit logs must be retained for 7 years and be tamper-evident.",
        "schemaVersion": 1,
    },
]

POLICIES = [
    {
        "_id": "pol-001",
        "title": "Internal Policy: Data Encryption",
        "department": "Engineering",
        "text": "We encrypt customer data at rest with AES-256. Key management is via a cloud KMS.",
        "schemaVersion": 1,
    },
    {
        "_id": "pol-002",
        "title": "Internal Policy: Network TLS",
        "department": "Infrastructure",
        "text": "All services must use TLS 1.2 or newer for external communication.",
        "schemaVersion": 1,
    },
]


def compute_embedding(text: str):
    # Use OpenAI embeddings if available; normalize to floats
    if not OPENAI_API_KEY:
        return None
    resp = openai.Embedding.create(input=text, model="text-embedding-3")
    emb = resp["data"][0]["embedding"]
    if len(emb) != EMBEDDING_DIMS:
        print(f"Warning: embedding length {len(emb)} != EMBEDDING_DIMS({EMBEDDING_DIMS})")
    return emb


def upsert_collection(collection_name, docs):
    db = get_db()
    coll = db[collection_name]
    for d in docs:
        doc = d.copy()
        if OPENAI_API_KEY:
            emb = compute_embedding(doc["text"])
            if emb:
                doc["embedding"] = emb
        doc["updatedAt"] = int(time.time())
        coll.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    print(f"Upserted {len(docs)} docs into {collection_name}")


if __name__ == "__main__":
    upsert_collection("regulations", REGULATIONS)
    upsert_collection("policies", POLICIES)
    print("Seed complete.")
