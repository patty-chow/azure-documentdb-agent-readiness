"""
Seed sample regulatory clauses and internal policy documents into DocumentDB.
Computes embeddings via OpenAI and upserts documents so re-running is safe.
"""
import os
import time
from dotenv import load_dotenv
from src.db import get_db
import openai
import numpy as np

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
EMBED_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

REG_DOCS = [
    {
        "_id": "reg-1",
        "title": "PCI Requirement: MFA for Remote Admin",
        "source": "PCI-DSS",
        "section": "8.3",
        "content": "All remote administrative access to cardholder data environments must be protected with multi-factor authentication.",
    },
    {
        "_id": "reg-2",
        "title": "GDPR Personal Data Access",
        "source": "GDPR",
        "section": "15",
        "content": "Data subjects must be able to request access to their personal data and the controller must provide a copy of the data upon request within one month.",
    },
    {
        "_id": "reg-3",
        "title": "SOX Financial Controls",
        "source": "SOX",
        "section": "302",
        "content": "Company officers must certify the accuracy of financial reports and maintain internal controls to ensure completeness and accuracy.",
    },
]

POLICY_DOCS = [
    {
        "_id": "pol-1",
        "title": "Admin Access Policy",
        "owner": "IT Security",
        "content": "Administrators must use strong passwords and rotate them every 90 days. Remote administrative access is allowed without additional factors.",
    },
    {
        "_id": "pol-2",
        "title": "Data Subject Requests",
        "owner": "Privacy Office",
        "content": "Employees must escalate data access requests to the Privacy Office. The Privacy Office aims to respond within 45 days.",
    },
]


def embed_text(text: str):
    # Simple wrapper for OpenAI embeddings
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY is required for computing embeddings")
    resp = openai.Embedding.create(model=EMBED_MODEL, input=text)
    vec = resp["data"][0]["embedding"]
    # Normalize for cosine similarity
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = (arr / norm).tolist()
    return arr


def upsert_collection(collection, docs):
    for d in docs:
        text = d.get("content", "")
        # compute embedding
        print(f"Embedding doc {d["_id"]} ...")
        emb = embed_text(text)
        d["embedding"] = emb
        d["embedding_model"] = EMBED_MODEL
        d["embedding_dims"] = len(emb)
        # upsert
        collection.update_one({"_id": d["_id"]}, {"$set": d}, upsert=True)


if __name__ == "__main__":
    db = get_db()
    reg_coll = db["regulatory"]
    pol_coll = db["internal_policies"]

    print("Seeding regulatory documents...")
    upsert_collection(reg_coll, REG_DOCS)
    print("Seeding internal policy documents...")
    upsert_collection(pol_coll, POLICY_DOCS)

    # create a text index on the content field for convenience (safe operation)
    print("Creating text index on content fields (if not exists)...")
    reg_coll.create_index([("content", "text")], name="content_text_idx")
    pol_coll.create_index([("content", "text")], name="content_text_idx")

    print("Seeding complete.")
