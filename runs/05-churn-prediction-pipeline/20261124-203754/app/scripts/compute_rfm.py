"""
Compute RFM per customer using an aggregation on the transactions collection and upsert into customers collection.
R = days since last purchase (lower is better), F = frequency (#transactions), M = monetary (sum amount)
This script computes raw values and a simple 1-5 score per dimension using quantiles.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from src.db import get_db
import numpy as np


def compute_rfm():
    db = get_db()
    tx_coll = db["transactions"]
    cust_coll = db["customers"]

    pipeline = [
        {"$group": {
            "_id": "$customer_id",
            "recency_ts": {"$max": "$timestamp"},
            "frequency": {"$sum": 1},
            "monetary": {"$sum": "$amount"}
        }}
    ]
    print("Running aggregation to compute RFM stats...")
    results = list(tx_coll.aggregate(pipeline))
    print(f"Aggregated RFM for {len(results)} customers")
    now = datetime.utcnow()
    # compute recency in days
    recencies = []
    freqs = []
    monos = []
    for r in results:
        rec_days = (now - r["recency_ts"]).days if r.get("recency_ts") else 9999
        recencies.append(rec_days)
        freqs.append(r.get("frequency", 0))
        monos.append(r.get("monetary", 0.0))
    # Use numpy percentiles to map to 1-5 scores
    def to_score(arr):
        # higher is better except for recency
        p = np.percentile(arr, [20, 40, 60, 80])
        def scorer(v):
            if v <= p[0]:
                return 1
            elif v <= p[1]:
                return 2
            elif v <= p[2]:
                return 3
            elif v <= p[3]:
                return 4
            else:
                return 5
        return scorer

    rec_scorer = to_score(recencies)
    freq_scorer = to_score(freqs)
    mon_scorer = to_score(monos)

    # Upsert RFM results
    for r, rec_d in zip(results, recencies):
        cust_id = r["_id"]
        freq = r.get("frequency", 0)
        mono = r.get("monetary", 0.0)
        r_score = rec_scorer(rec_d)
        f_score = freq_scorer(freq)
        m_score = mon_scorer(mono)
        # Compose a simple RFM vector
        rfm_vector = [r_score, f_score, m_score]
        cust_coll.update_one({"_id": cust_id}, {"$set": {
            "rfm": {
                "recency_days": rec_d,
                "frequency": freq,
                "monetary": mono,
                "score": {"r": r_score, "f": f_score, "m": m_score},
                "rfm_vector": rfm_vector
            }
        }}, upsert=False)
    print("RFM upsert complete.")

if __name__ == "__main__":
    compute_rfm()
