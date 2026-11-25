from datetime import datetime, timedelta
from pymongo import InsertOne
from bson import ObjectId

# Utility: build month boundaries (list of datetimes at month starts)
def month_starts_between(start_dt, end_dt):
    months = []
    cur = datetime(start_dt.year, start_dt.month, 1)
    while cur <= end_dt:
        months.append(cur)
        if cur.month == 12:
            cur = datetime(cur.year + 1, 1, 1)
        else:
            cur = datetime(cur.year, cur.month + 1, 1)
    return months


def generate_cohort_snapshot(db):
    """Runs aggregation over customers + events and writes one snapshot document to cohort_snapshots.

    Snapshot document shape:
      {
        _id: ObjectId,
        snapshot_month: "YYYY-MM-DD" (date when snapshot was taken),
        generated_at: ISODate,
        buckets: [ { start: ISODate, end: ISODate, acquired_label: "YYYY-MM", count: N, retained30: n30, retained60: n60, retained90: n90, channels: { ... }, products: { ... } }, ... ]
      }
    """
    customers = db.customers
    events = db.events
    snapshots = db.cohort_snapshots

    # Determine range of acquisition dates present in customers (idempotent if empty)
    stat = customers.aggregate([
        {"$group": {"_id": None, "min": {"$min": "$acquired_at"}, "max": {"$max": "$acquired_at"}}}
    ])
    stat = list(stat)
    if not stat or stat[0]["min"] is None:
        # no customers — nothing to do
        snapshot = {
            "snapshot_month": datetime.utcnow().strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow(),
            "buckets": []
        }
        snapshots.insert_one(snapshot)
        return snapshot

    min_dt = stat[0]["min"]
    max_dt = stat[0]["max"]

    # build month boundaries for $bucket: from first month to month after last
    starts = month_starts_between(min_dt, max_dt)
    # create boundary list as datetimes, append one extra month end
    if not starts:
        starts = [min_dt]
    # last boundary = first day of month after max_dt
    last = starts[-1]
    if last.month == 12:
        after_last = datetime(last.year + 1, 1, 1)
    else:
        after_last = datetime(last.year, last.month + 1, 1)
    boundaries = starts + [after_last]

    # Build aggregation pipeline
    pipeline = [
        # attach events for each customer (lookup)
        {
            "$lookup": {
                "from": "events",
                "localField": "customer_id",
                "foreignField": "customer_id",
                "as": "events"
            }
        },
        # compute retention flags per customer
        {
            "$addFields": {
                "retained30": {
                    "$gt": [
                        {"$size": {"$filter": {"input": "$events", "as": "e", "cond": {"$lte": ["$$e.event_date", {"$dateAdd": {"startDate": "$acquired_at", "unit": "day", "amount": 30}}]}}}},
                        0
                    ]
                },
                "retained60": {
                    "$gt": [
                        {"$size": {"$filter": {"input": "$events", "as": "e", "cond": {"$lte": ["$$e.event_date", {"$dateAdd": {"startDate": "$acquired_at", "unit": "day", "amount": 60}}]}}}},
                        0
                    ]
                },
                "retained90": {
                    "$gt": [
                        {"$size": {"$filter": {"input": "$events", "as": "e", "cond": {"$lte": ["$$e.event_date", {"$dateAdd": {"startDate": "$acquired_at", "unit": "day", "amount": 90}}]}}}},
                        0
                    ]
                }
            }
        },
        # use $bucket to group by acquisition month using boundaries
        {
            "$bucket": {
                "groupBy": "$acquired_at",
                "boundaries": boundaries,
                "default": None,
                "output": {
                    "count": {"$sum": 1},
                    "retained30": {"$sum": {"$cond": ["$retained30", 1, 0]}},
                    "retained60": {"$sum": {"$cond": ["$retained60", 1, 0]}},
                    "retained90": {"$sum": {"$cond": ["$retained90", 1, 0]}},
                    "channels": {"$push": "$channel"},
                    "products": {"$push": "$primary_product_id"}
                }
            }
        },
        # after bucketing, compute breakdowns (channel/product counts)
        {
            "$project": {
                "start": "$_id",
                "end": 1,
                "count": 1,
                "retained30": 1,
                "retained60": 1,
                "retained90": 1,
                "channel_counts": {
                    "$arrayToObject": {
                        "$map": {
                            "input": {"$setUnion": ["$channels", []]},
                            "as": "c",
                            "in": ["$$c", {"$size": {"$filter": {"input": "$channels", "as": "cc", "cond": {"$eq": ["$$cc", "$$c"]}}}}]
                        }
                    }
                },
                "product_counts": {
                    "$arrayToObject": {
                        "$map": {
                            "input": {"$setUnion": ["$products", []]},
                            "as": "p",
                            "in": ["$$p", {"$size": {"$filter": {"input": "$products", "as": "pp", "cond": {"$eq": ["$$pp", "$$p"]}}}}]
                        }
                    }
                }
            }
        }
    ]

    # Run aggregation
    agg = list(customers.aggregate(pipeline))

    # Transform results to snapshot buckets
    buckets = []
    for b in agg:
        start = b.get("start")
        end = b.get("end")
        label = None
        if start:
            label = start.strftime("%Y-%m")
        buckets.append({
            "start": start,
            "end": end,
            "label": label,
            "count": b.get("count", 0),
            "retained30": b.get("retained30", 0),
            "retained60": b.get("retained60", 0),
            "retained90": b.get("retained90", 0),
            "channels": b.get("channel_counts", {}),
            "products": b.get("product_counts", {})
        })

    snapshot = {
        "snapshot_month": datetime.utcnow().strftime("%Y-%m-%d"),
        "generated_at": datetime.utcnow(),
        "buckets": buckets
    }

    snapshots.insert_one(snapshot)
    return snapshot


def list_snapshots(db, limit=20):
    docs = list(db.cohort_snapshots.find({}, {"buckets": 0}).sort("generated_at", -1).limit(limit))
    return docs


def get_snapshot(db, generated_at_date_str):
    return db.cohort_snapshots.find_one({"snapshot_month": generated_at_date_str})
