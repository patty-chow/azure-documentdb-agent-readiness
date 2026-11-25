"""Seed sample position documents into sample_banking_13.positions (idempotent upserts)."""
import os
import random
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to Azure DocumentDB")

client = MongoClient(DOCUMENTDB_URI, tls=True)
db = client.get_database("sample_banking_13")
coll = db.get_collection("positions")

# Generate deterministic-ish sample data
random.seed(42)

positions = []
for i in range(1, 21):
    rwa = random.randint(1_000, 50_000)
    cet1 = round(rwa * random.uniform(0.03, 0.12), 2)  # CET1 between 3% and 12% of RWA
    total = round(rwa * random.uniform(0.06, 0.16), 2)  # total capital between 6% and 16%
    positions.append({
        "position_id": f"pos_{i}",
        "account": f"ACCT{i:04d}",
        "booked_date": datetime.utcnow(),
        "risk_weighted_assets": rwa,
        "capital": {"cet1": cet1, "total": total},
        "schemaVersion": "1.0"
    })

# Upsert idempotently
ops = []
for p in positions:
    ops.append(UpdateOne({"position_id": p["position_id"]}, {"$set": p}, upsert=True))

result = coll.bulk_write(ops)
print(f"Upserted: {result.upserted_count}, Modified: {result.modified_count}")
