import json
from datetime import datetime
from pymongo import ASCENDING
from bson.son import SON

DB_NAME = "sample_fintech_09"
COLLECTION = "transactions"

def ensure_indexes(db):
    coll = db[COLLECTION]
    # compound index on wallet_address and timestamp to support time-range queries
    coll.create_index([("wallet_address", ASCENDING), ("timestamp", ASCENDING)], name="idx_wallet_time")


def aggregation_tool(db, wallet_address, days=None):
    """Run the aggregation pipeline that groups transactions by day for a given wallet.
    Returns a JSON-serializable list of { date: YYYY-MM-DD, total: float, count: int }.
    """
    coll = db[COLLECTION]

    match_stage = {"$match": {"wallet_address": wallet_address}}
    # Project a date string (YYYY-MM-DD) derived from timestamp
    project_stage = {
        "$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "amount": 1,
        }
    }
    group_stage = {
        "$group": {
            "_id": "$date",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }
    }
    sort_stage = {"$sort": SON([("_id", 1)])}

    pipeline = [match_stage, project_stage, group_stage, sort_stage]
    cursor = coll.aggregate(pipeline)

    results = []
    for doc in cursor:
        results.append({"date": doc["_id"], "total": float(doc["total"]), "count": int(doc["count"])})
    return results


def run_aggregation_and_index(db, wallet_address):
    ensure_indexes(db)
    return aggregation_tool(db, wallet_address)
