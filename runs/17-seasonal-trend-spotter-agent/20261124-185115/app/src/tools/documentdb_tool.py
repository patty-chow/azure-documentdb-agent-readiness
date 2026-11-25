"""
DocumentDB aggregation tool: computes sales velocity across seasons.
Provides a function `seasonal_sales_velocity` that returns aggregated stats per category.
"""
import os
from pymongo import MongoClient
from datetime import datetime

DB_NAME = "sample_retail_17"
COLLECTION = "sales"


def get_client():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI is not set in the environment")
    # Singleton pattern is handled by module-level caching
    global _client
    try:
        _client
    except NameError:
        _client = MongoClient(uri)
    return _client


def _season(dt):
    m = dt.month
    if m in (12, 1, 2):
        return "winter"
    if m in (3, 4, 5):
        return "spring"
    if m in (6, 7, 8):
        return "summer"
    return "autumn"


def seasonal_sales_velocity(window_days=30, reference_date=None, top_n=10):
    """
    Compute sales velocity per category across seasons using an aggregation pipeline.
    Returns a list of dicts: {category, season, total_quantity, total_value, avg_price}
    """
    client = get_client()
    db = client[DB_NAME]
    coll = db[COLLECTION]
    if reference_date is None:
        reference_date = datetime.utcnow()

    # We'll compute totals per category and season for the trailing window_days
    from datetime import timedelta
    start = reference_date - timedelta(days=window_days)

    pipeline = [
        {"$match": {"sale_date": {"$gte": start, "$lte": reference_date}}},
        {"$addFields": {"season": {"$switch": {
            "branches": [
                {"case": {"$in": [{"$month": "$sale_date"}, [12,1,2]]}, "then": "winter"},
                {"case": {"$in": [{"$month": "$sale_date"}, [3,4,5]]}, "then": "spring"},
                {"case": {"$in": [{"$month": "$sale_date"}, [6,7,8]]}, "then": "summer"},
            ],
            "default": "autumn"
        }}}},
        {"$group": {"_id": {"category": "$category", "season": "$season"},
                     "total_quantity": {"$sum": "$quantity"},
                     "total_value": {"$sum": {"$multiply": ["$quantity", "$price"]}},
                     "avg_price": {"$avg": "$price"}}},
        {"$project": {"category": "$_id.category", "season": "$_id.season", "total_quantity": 1, "total_value": 1, "avg_price": 1, "_id": 0}},
        {"$sort": {"total_quantity": -1}},
        {"$limit": top_n}
    ]

    results = list(coll.aggregate(pipeline))
    return results


if __name__ == '__main__':
    import json
    out = seasonal_sales_velocity()
    print(json.dumps(out, default=str, indent=2))
