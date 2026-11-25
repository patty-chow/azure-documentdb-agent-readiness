"""
Idempotent seed script for sample fraud patterns.
Computes embeddings locally (sentence-transformers) and upserts into
sample_fintech_01.fraud_patterns collection.
"""
import os
import time
from docdb_client import get_db
from embeddings import embed_many

SAMPLE_PATTERNS = [
    {
        "pattern_name": "rapid_small_transactions",
        "description": "Multiple small transactions in quick succession to a new payee",
    },
    {
        "pattern_name": "high_amount_new_payee",
        "description": "Single large transfer to a recently added payee",
    },
    {
        "pattern_name": "odd_location",
        "description": "Transaction from a geographic location not typical for the account",
    },
    {
        "pattern_name": "mismatched_device",
        "description": "Transaction initiated from a different device fingerprint than usual",
    },
    {
        "pattern_name": "velocity_login_and_tx",
        "description": "Login immediately followed by high-value transactions",
    },
]


def main():
    db = get_db()
    coll = db["fraud_patterns"]

    texts = [p["description"] for p in SAMPLE_PATTERNS]
    vecs = embed_many(texts)

    now = int(time.time())
    for p, v in zip(SAMPLE_PATTERNS, vecs):
        doc = {
            "pattern_name": p["pattern_name"],
            "description": p["description"],
            "ts": now,
            "vector": v,
            "model": "all-MiniLM-L6-v2",
            "dims": len(v),
            "schemaVersion": 1,
        }
        # upsert by pattern_name to be idempotent
        coll.replace_one({"pattern_name": p["pattern_name"]}, doc, upsert=True)
        print("Upserted pattern", p["pattern_name"])

    print("Seed complete. Inserted/updated {} patterns.".format(len(SAMPLE_PATTERNS)))


if __name__ == "__main__":
    main()
