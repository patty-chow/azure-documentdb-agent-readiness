import os
import random
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_banking_14")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "complaints")

SAMPLE_TEMPLATES = [
    "I was charged an unexpected fee on my checking account.",
    "My credit card payment was not posted and now I have a late fee.",
    "The mobile app crashes when I try to transfer money.",
    "I can't log in to my online banking; password reset failed.",
    "My loan payment schedule changed without notice.",
    "I received a declined transaction even though I have funds.",
]

NUM_DOCS = 120


def generate_docs(n=NUM_DOCS):
    docs = []
    for i in range(n):
        txt = random.choice(SAMPLE_TEMPLATES)
        doc = {
            "external_id": f"seed-{i}",
            "complaint_text": txt,
            "created_at": datetime.utcnow(),
            "customer_id": f"cust-{random.randint(1,50)}",
            # classification fields left null for pipeline to fill
        }
        docs.append(doc)
    return docs


def seed():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set in env")
    client = MongoClient(DOCUMENTDB_URI)
    db = client[DATABASE_NAME]
    coll = db[COLLECTION_NAME]
    docs = generate_docs()
    for doc in docs:
        coll.update_one({"external_id": doc["external_id"]}, {"$set": doc}, upsert=True)
    print(f"Upserted {len(docs)} sample documents into {DATABASE_NAME}.{COLLECTION_NAME}")

if __name__ == "__main__":
    seed()
