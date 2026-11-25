from datetime import datetime, timedelta
from pymongo import ASCENDING, DESCENDING
from .db import get_db
from bson.objectid import ObjectId

# Collections: customers, events, cohort_snapshots

def ensure_indexes():
    db = get_db()
    db.customers.create_index([("customer_id", ASCENDING)], unique=True)
    db.customers.create_index([("acquired_at", ASCENDING)])
    db.customers.create_index([("channel", ASCENDING)])

    db.events.create_index([("customer_id", ASCENDING)])
    db.events.create_index([("event_date", ASCENDING)])
    db.events.create_index([("product_id", ASCENDING)])


def _month_starts_list(months_back, now=None):
    if now is None:
        now = datetime.utcnow()
    starts = []
    # produce `months_back` entries ending with current month start
    for i in range(months_back-1, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        starts.append(datetime(year, month, 1))
    return starts


def compute_and_store_snapshot(snapshot_name=None, months_back=12):
    db = get_db()
    now = datetime.utcnow()
    month_starts = _month_starts_list(months_back, now)

    buckets = []
    for start in month_starts:
        # month end is next month start
        if start.month == 12:
            end = datetime(start.year + 1, 1, 1)
        else:
            end = datetime(start.year, start.month + 1, 1)
        # find customers acquired in [start, end)
        customers = list(db.customers.find({"acquired_at": {"$gte": start, "$lt": end}}, {"customer_id":1, "channel":1, "acquired_at":1}))
        total = len(customers)
        cust_ids = [c["customer_id"] for c in customers]
        # compute retention counts by checking events within 30/60/90 days of acquired_at per customer
        ret30 = 0
        ret60 = 0
        ret90 = 0
        channel_breakdown = {}
        product_breakdown = {}
        for c in customers:
            cid = c["customer_id"]
            acquired = c["acquired_at"]
            # count distinct events in windows
            # 30 days
            d30 = acquired + timedelta(days=30)
            d60 = acquired + timedelta(days=60)
            d90 = acquired + timedelta(days=90)
            e30 = db.events.find_one({"customer_id": cid, "event_date": {"$gt": acquired, "$lte": d30}})
            e60 = db.events.find_one({"customer_id": cid, "event_date": {"$gt": acquired, "$lte": d60}})
            e90 = db.events.find_one({"customer_id": cid, "event_date": {"$gt": acquired, "$lte": d90}})
            if e30:
                ret30 += 1
            if e60:
                ret60 += 1
            if e90:
                ret90 += 1
            ch = c.get("channel", "unknown")
            channel_breakdown.setdefault(ch, {"count":0, "ret30":0, "ret60":0, "ret90":0})
            channel_breakdown[ch]["count"] += 1
            if e30:
                channel_breakdown[ch]["ret30"] += 1
            if e60:
                channel_breakdown[ch]["ret60"] += 1
            if e90:
                channel_breakdown[ch]["ret90"] += 1
            # product breakdown: look up purchases in events for this customer in first 90 days
            prods = db.events.find({"customer_id": cid, "event_date": {"$gt": acquired, "$lte": d90}}, {"product_id":1})
            for p in prods:
                pid = p.get("product_id", "unknown")
                product_breakdown.setdefault(pid, {"count":0})
                product_breakdown[pid]["count"] += 1

        bucket = {
            "cohort_start": start,
            "cohort_end": end,
            "total_customers": total,
            "retention": {"30d": ret30, "60d": ret60, "90d": ret90},
            "channel_breakdown": channel_breakdown,
            "product_breakdown": product_breakdown
        }
        buckets.append(bucket)

    snapshot = {
        "created_at": now,
        "months_back": months_back,
        "buckets": buckets,
        "schemaVersion": 1,
        "snapshot_name": snapshot_name or f"cohort_snapshot_{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    }
    db.cohort_snapshots.insert_one(snapshot)
    return snapshot


def list_snapshots(limit=20):
    db = get_db()
    return list(db.cohort_snapshots.find().sort([("created_at", DESCENDING)]).limit(limit))


def get_snapshot_by_month(cohort_month):
    db = get_db()
    # cohort_month like YYYY-MM
    return db.cohort_snapshots.find_one({"snapshot_name": {"$regex": cohort_month}})
