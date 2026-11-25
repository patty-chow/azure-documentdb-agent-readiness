from datetime import datetime
from typing import List, Dict, Any

from pymongo import ASCENDING
from pymongo.collection import Collection

from src.db import get_positions_collection


BUCKET_BOUNDARIES = [0, 1, 3, 5, 10, 100]
BUCKET_LABELS = ["0-1y", "1-3y", "3-5y", "5-10y", ">10y"]


def _ensure_index(coll: Collection):
    # create a simple index to support aggregations and filters
    coll.create_index([("maturity_date", ASCENDING), ("rate_type", ASCENDING)], name="idx_maturity_rate_type")


def summarize_positions() -> List[Dict[str, Any]]:
    """Run an aggregation pipeline that buckets by maturity and groups by rate_type.
    Returns a list of summaries: [{bucket: str, rate_type: str, notional: float, count: int, avg_coupon: float}]
    """
    coll = get_positions_collection()
    # ensure index exists (idempotent)
    _ensure_index(coll)

    now = datetime.utcnow()

    # Pipeline: compute maturity years, then bucket, then group by bucket + rate_type
    pipeline = [
        {
            "$addFields": {
                "maturity_years": {
                    "$divide": [{"$subtract": ["$maturity_date", now]}, 1000.0 * 60 * 60 * 24 * 365]
                }
            }
        },
        {
            "$bucket": {
                "groupBy": "$maturity_years",
                "boundaries": BUCKET_BOUNDARIES,
                "default": ">10y",
                "output": {
                    "docs": {"$push": "$$ROOT"},
                    "total_notional": {"$sum": "$notional"},
                    "count": {"$sum": 1}
                }
            }
        },
        {"$unwind": "$docs"},
        {
            "$group": {
                "_id": {"bucket": "$_id", "rate_type": "$docs.rate_type"},
                "notional": {"$sum": "$docs.notional"},
                "count": {"$sum": 1},
                "avg_coupon": {"$avg": "$docs.coupon_rate"}
            }
        },
        {
            "$project": {
                "bucket": "$_id.bucket",
                "rate_type": "$_id.rate_type",
                "notional": 1,
                "count": 1,
                "avg_coupon": 1,
                "_id": 0
            }
        },
        {"$sort": {"bucket": 1, "rate_type": 1}}
    ]

    results = list(coll.aggregate(pipeline))
    # Normalize bucket numeric boundaries to labels if needed
    # The pipeline's _id.bucket will be a number for numeric buckets (lower-bound). Map to labels
    def bucket_label(b):
        try:
            bnum = float(b)
            # find index of boundary
            for i in range(len(BUCKET_BOUNDARIES) - 1):
                if BUCKET_BOUNDARIES[i] == bnum:
                    return BUCKET_LABELS[i]
        except Exception:
            # default fallback
            return str(b)
        return str(b)

    for r in results:
        r["bucket"] = bucket_label(r["bucket"]) if r["bucket"] not in BUCKET_LABELS else r["bucket"]
    return results


if __name__ == "__main__":
    from pprint import pprint

    print("Running aggregation against", get_positions_collection().database.name)
    pprint(summarize_positions())
