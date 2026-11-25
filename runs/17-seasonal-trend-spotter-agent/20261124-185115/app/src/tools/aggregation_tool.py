from datetime import datetime
from src.db import get_db

# Aggregation pipeline to compute sales velocity per category per season
# season is derived from sale_date month

SEASON_EXPR = {
    "$switch": {
        "branches": [
            {"case": {"$in": [{"$month": "$sale_date"}, [12, 1, 2]]}, "then": "winter"},
            {"case": {"$in": [{"$month": "$sale_date"}, [3, 4, 5]]}, "then": "spring"},
            {"case": {"$in": [{"$month": "$sale_date"}, [6, 7, 8]]}, "then": "summer"},
        ],
        "default": "fall",
    }
}


def seasonal_velocity(top_n=10, since_years=1):
    db = get_db()
    coll = db.sales
    now = datetime.utcnow()
    from_date = datetime(now.year - since_years, now.month, now.day)

    pipeline = [
        {"$match": {"sale_date": {"$gte": from_date}}},
        {"$addFields": {"season": SEASON_EXPR}},
        {"$group": {
            "_id": {"category": "$category", "season": "$season"},
            "total_quantity": {"$sum": "$quantity"},
            "total_revenue": {"$sum": {"$multiply": ["$quantity", "$price"]}},
            "count_tx": {"$sum": 1}
        }},
        {"$project": {
            "category": "$_id.category",
            "season": "$_id.season",
            "total_quantity": 1,
            "total_revenue": 1,
            "count_tx": 1,
            "_id": 0
        }},
        {"$sort": {"total_quantity": -1}}
    ]

    results = list(coll.aggregate(pipeline))
    return results
