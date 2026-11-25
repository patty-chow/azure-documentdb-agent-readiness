"""Seed sample data into the DOCUMENTDB cluster. Idempotent upserts by _id."""
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("DOCUMENTDB_URI")
if not uri:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required. Copy .env.example to .env and fill it.")

db_name = os.environ.get("DOCUMENTDB_DATABASE", "sample_banking_01")
client = MongoClient(uri)
db = client[db_name]
transactions = db.transactions
accounts = db.accounts

# Create indexes if not exist - rely on server-side idempotency
print("Ensuring indexes...")
transactions.create_index([("from_account", 1)])
transactions.create_index([("to_account", 1)])
transactions.create_index([("from_account", 1), ("timestamp", 1)])

# Seed accounts
now = datetime.utcnow()
ops = []
accounts_data = [
    {"_id": "A1", "owner": "Alice"},
    {"_id": "A2", "owner": "Bob"},
    {"_id": "A3", "owner": "Carol"},
    {"_id": "A4", "owner": "Dave"},
    {"_id": "A5", "owner": "Eve"},
    {"_id": "A6", "owner": "Mallory"},
]
for a in accounts_data:
    ops.append(UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True))

if ops:
    accounts.bulk_write(ops)

# Seed transactions to show typologies:
# 1) Structuring: many small deposits into A2 within 1 day
# 2) Rapid pass-through: A1 -> A3 -> A4 -> A5 within minutes
# 3) Circular transfer: A6 -> A4 -> A6 (cycle)

print("Seeding transactions...")
transactions_ops = []
# Structuring: 5 small incoming transactions to A2
t0 = now - timedelta(days=1)
for i in range(5):
    tx = {
        "_id": f"struct_{i}",
        "from_account": f"F{i}",
        "to_account": "A2",
        "amount": 900,  # below reporting threshold
        "timestamp": (t0 + timedelta(hours=i)).isoformat(),
    }
    transactions_ops.append(UpdateOne({"_id": tx["_id"]}, {"$set": tx}, upsert=True))

# Rapid pass-through
tp = now - timedelta(hours=2)
chain = [("A1","A3"),("A3","A4"),("A4","A5")]
for idx,(fa,ta) in enumerate(chain):
    tx = {
        "_id": f"rapid_{idx}",
        "from_account": fa,
        "to_account": ta,
        "amount": 50000,
        "timestamp": (tp + timedelta(minutes=idx*2)).isoformat(),
        "linked_tx_ids": []
    }
    transactions_ops.append(UpdateOne({"_id": tx["_id"]}, {"$set": tx}, upsert=True))

# Circular transfers
tc = now - timedelta(hours=3)
circle = [("A6","A4"),("A4","A6")]
for idx,(fa,ta) in enumerate(circle):
    tx = {
        "_id": f"circ_{idx}",
        "from_account": fa,
        "to_account": ta,
        "amount": 20000,
        "timestamp": (tc + timedelta(minutes=idx*5)).isoformat(),
    }
    transactions_ops.append(UpdateOne({"_id": tx["_id"]}, {"$set": tx}, upsert=True))

if transactions_ops:
    transactions.bulk_write(transactions_ops)

print("Seed complete. Inserted/updated sample accounts and transactions into database:", db_name)
