"""
Seed synthetic customers and transactions into the sample DB.
Creates 'customers' and 'transactions' collections and inserts ~200 customers.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from datetime import datetime, timedelta
from uuid import uuid4
from src.db import get_db

NUM_CUSTOMERS = 200
MAX_TX_PER_CUSTOMER = 20


def seed():
    db = get_db()
    customers = []
    transactions = []
    now = datetime.utcnow()
    for i in range(NUM_CUSTOMERS):
        cust_id = str(uuid4())
        churn = random.random() < 0.12  # 12% churned in sample
        customers.append({
            "_id": cust_id,
            "schemaVersion": 1,
            "churn": churn,
            "rfm": None,
            "rfm_embedding": []
        })
        num_tx = random.randint(1, MAX_TX_PER_CUSTOMER)
        for t in range(num_tx):
            days_ago = random.randint(0, 365)
            tx_date = now - timedelta(days=days_ago)
            amount = round(random.uniform(5.0, 500.0), 2)
            transactions.append({
                "_id": str(uuid4()),
                "customer_id": cust_id,
                "amount": amount,
                "timestamp": tx_date
            })
    # Insert customers and transactions with simple idempotency: replace_many
    cust_coll = db["customers"]
    tx_coll = db["transactions"]
    print(f"Inserting {len(customers)} customers and {len(transactions)} transactions...")
    # We'll upsert each customer to avoid duplicates on re-run
    for c in customers:
        cust_coll.replace_one({"_id": c["_id"]}, c, upsert=True)
    # For transactions, insert many but skip if tx already exists
    existing_ids = set()
    for doc in tx_coll.find({}, {"_id": 1}):
        existing_ids.add(str(doc["_id"]))
    to_insert = [t for t in transactions if t["_id"] not in existing_ids]
    if to_insert:
        tx_coll.insert_many(to_insert)
    print("Seed complete.")


if __name__ == "__main__":
    seed()
