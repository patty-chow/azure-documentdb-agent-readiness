import os
import time
import random
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "sample_customer_360_10"
COLLECTION = "kb_documents"

uri = os.environ.get("DOCUMENTDB_URI")
if not uri:
    print("DOCUMENTDB_URI not set. Set it in environment or .env file. Exiting.")
    raise SystemExit(1)

# Singleton client
client = MongoClient(uri)
db = client[DB_NAME]
col = db[COLLECTION]

# Create some synthetic KB articles and past resolutions
TITLES = [
    "How to reset a password",
    "SSO troubleshooting steps",
    "Database connection timeout causes",
    "Configuring email notifications",
    "Disk space cleanup guide",
    "Service A circuit-breaker behavior",
    "OAuth token refresh failures",
    "API rate limit handling",
    "SSL certificate rotation",
    "User on-boarding checklist",
]


def make_kb(i):
    title = random.choice(TITLES) + f" (KB {i})"
    content = f"This KB article explains {title}. Steps: step1, step2, step3. Details {i}."
    return {
        "type": "kb",
        "title": title,
        "content": content,
        "metadata": {"source": "kb", "seed_index": i},
        "created_at": datetime.utcnow(),
    }


def make_resolution(i):
    title = f"Resolved ticket #{i}"
    content = f"Resolution details for ticket {i}. Root cause: transient issue. Fix applied: restart service. Notes {i}."
    return {
        "type": "resolution",
        "title": title,
        "content": content,
        "metadata": {"source": "resolution", "seed_index": i},
        "created_at": datetime.utcnow(),
    }


def seed(n_kb=30, n_res=30):
    docs = []
    for i in range(n_kb):
        docs.append(make_kb(i))
    for i in range(n_res):
        docs.append(make_resolution(i))

    # Upsert documents based on metadata.seed_index to be idempotent
    for d in docs:
        query = {"metadata.seed_index": d["metadata"]["seed_index"], "type": d["type"]}
        update = {"$set": d}
        col.update_one(query, update, upsert=True)

    # Create simple non-vector indexes for prefiltering
    col.create_index([("type", 1)])
    col.create_index([("created_at", -1)])
    print(f"Seeded {len(docs)} documents into {DB_NAME}.{COLLECTION}")


if __name__ == "__main__":
    seed()
    client.close()
