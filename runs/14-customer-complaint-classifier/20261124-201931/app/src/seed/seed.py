"""Seed script to populate synthetic complaints into DocumentDB
Usage: python -m src.seed.seed --uri "$DOCUMENTDB_URI" --db sample_banking_14
"""
import argparse
import os
import random
from datetime import datetime
from pymongo import MongoClient

SAMPLE_TEXTS = [
    "I was charged a late fee even though I paid on time.",
    "My mortgage payment amount changed without notice.",
    "Unauthorized transaction on my checking account.",
    "Unable to open savings account online, error during signup.",
    "Loan interest rate was miscalculated on my statement.",
]
CATEGORIES = ["credit-card", "mortgage", "checking", "savings", "loan", "other"]


def make_doc(i):
    return {
        "external_id": f"seed-{i}",
        "complaint_text": random.choice(SAMPLE_TEXTS) + f" (case {i})",
        "created_at": datetime.utcnow(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default=os.environ.get("DOCUMENTDB_URI"))
    parser.add_argument("--db", default=os.environ.get("DOCUMENTDB_DB_NAME", "sample_banking_14"))
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()
    if not args.uri:
        raise RuntimeError("DOCUMENTDB_URI required via --uri or environment")
    client = MongoClient(args.uri)
    coll = client[args.db]["complaints"]
    for i in range(args.count):
        doc = make_doc(i)
        coll.update_one({"external_id": doc["external_id"]}, {"$set": doc}, upsert=True)
    print(f"Seeded {args.count} documents into {args.db}.complaints")

if __name__ == "__main__":
    main()
