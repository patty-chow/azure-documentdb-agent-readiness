"""Compute per-branch summaries using aggregation with $facet and upsert into branch_summaries collection."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import get_db
from pymongo import UpdateOne
from datetime import datetime


def compute_and_store_summaries():
    db = get_db()
    tx = db.transactions
    branches = db.transactions.distinct("branchId")
    ops = []
    for b in branches:
        p = [
            {"$match": {"branchId": b}},
            {"$facet": {
                "totals": [
                    {"$group": {"_id": None, "totalVolume": {"$sum": "$amount"}, "txCount": {"$sum": 1}, "avgTicket": {"$avg": "$amount"}}}
                ],
                "productMix": [
                    {"$unwind": {"path": "$products"}},
                    {"$group": {"_id": "$products.productId", "count": {"$sum": "$products.qty"}}},
                    {"$project": {"productId": "$_id", "count": 1, "_id": 0}}
                ]
            }},
            {"$project": {
                "branchId": b,
                "totalVolume": {"$arrayElemAt": ["$totals.totalVolume", 0]},
                "txCount": {"$arrayElemAt": ["$totals.txCount", 0]},
                "avgTicket": {"$arrayElemAt": ["$totals.avgTicket", 0]},
                "productMix": "$productMix"
            }}
        ]
        res = list(db.transactions.aggregate(p))
        if res:
            r = res[0]
            r["lastUpdated"] = datetime.utcnow()
            # create a human-readable summaryText for simple lexical retrieval
            r["summaryText"] = f"Branch {b}: {r.get('txCount',0)} transactions, total ${r.get('totalVolume',0):.2f}, avg ${r.get('avgTicket',0):.2f}"
            ops.append(UpdateOne({"branchId": b}, {"$set": r}, upsert=True))
    if ops:
        result = db.branch_summaries.bulk_write(ops)
        return len(ops)
    return 0

if __name__ == '__main__':
    n = compute_and_store_summaries()
    print(f"Refreshed {n} branch summaries")
