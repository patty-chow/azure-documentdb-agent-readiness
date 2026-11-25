"""Seed script: create transactions collection, indexes, and insert synthetic transactions for ~10 branches."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from datetime import datetime, timedelta
from pymongo import ASCENDING, DESCENDING
from app.db import get_db


def seed(num_branches=10, tx_per_branch=500):
    db = get_db()
    tx_coll = db.transactions
    # Create indexes
    tx_coll.create_index([("branchId", ASCENDING)])
    tx_coll.create_index([("transactionDate", DESCENDING)])
    tx_coll.create_index([("products.productId", ASCENDING)])

    branches = [f"BR-{i:03d}" for i in range(1, num_branches+1)]
    # Idempotency: remove existing transactions for these branches
    tx_coll.delete_many({"branchId": {"$in": branches}})

    docs = []
    now = datetime.utcnow()
    for b in branches:
        for i in range(tx_per_branch):
            amount = round(random.uniform(5, 500), 2)
            days_ago = random.randint(0, 90)
            tx_date = now - timedelta(days=days_ago, seconds=random.randint(0, 86400))
            # sample products array
            num_products = random.choices([1,2,3], [0.6, 0.3, 0.1])[0]
            products = []
            for _ in range(num_products):
                pid = random.choice(["P-A","P-B","P-C","P-D","P-E"])
                qty = random.randint(1,3)
                products.append({"productId": pid, "qty": qty})
            docs.append({
                "branchId": b,
                "amount": amount,
                "transactionDate": tx_date,
                "products": products
            })
    # Bulk insert
    if docs:
        tx_coll.insert_many(docs)
    print(f"Inserted ~{len(docs)} transactions for {len(branches)} branches")

if __name__ == '__main__':
    seed()
