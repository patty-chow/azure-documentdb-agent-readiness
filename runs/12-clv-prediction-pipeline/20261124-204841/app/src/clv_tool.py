from datetime import datetime
from bson.son import SON
from src.db import get_customers_collection


def compute_customer_metrics(customer_id: str):
    """Run an aggregation to compute purchase_count, avg_order_value and tenure_days."""
    coll = get_customers_collection()
    pipeline = [
        {"$match": {"_id": customer_id}},
        {"$unwind": {"path": "$purchases", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$_id",
            "purchase_count": {"$sum": {"$cond": [{"$ifNull": ["$purchases", False]}, 1, 0]}},
            "avg_order_value": {"$avg": "$purchases.amount"},
            "first_purchase": {"$min": "$purchases.date"},
            "last_purchase": {"$max": "$purchases.date"},
        }},
    ]
    res = list(coll.aggregate(pipeline))
    if not res:
        return None
    row = res[0]
    # parse dates
    first = row.get("first_purchase")
    last = row.get("last_purchase")
    tenure_days = None
    if first and last:
        try:
            dt_first = datetime.fromisoformat(first)
            dt_last = datetime.fromisoformat(last)
            tenure_days = (dt_last - dt_first).days
        except Exception:
            tenure_days = None
    metrics = {
        "purchase_count": int(row.get("purchase_count", 0) or 0),
        "avg_order_value": float(row.get("avg_order_value") or 0.0),
        "tenure_days": tenure_days,
        "first_purchase": first,
        "last_purchase": last,
    }
    return metrics


def update_customer_clv(customer_id: str, clv_score: float, clv_tier: str, rationale: str):
    coll = get_customers_collection()
    res = coll.update_one({"_id": customer_id}, {"$set": {"clv_score": clv_score, "clv_tier": clv_tier, "clv_rationale": rationale}})
    return res.modified_count
