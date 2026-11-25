import json
from datetime import datetime, timedelta
from typing import List
from pymongo import ReturnDocument
import db

DB_NAME = "sample_retail_14"


def _serialize_doc(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if k == "_id":
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            try:
                json.dumps(v)
                out[k] = v
            except Exception:
                out[k] = str(v)
    return out


# Tool: get_competitor_prices
def get_competitor_prices_tool(text: str) -> str:
    """Expected input: 'sku:SKU-001;hours:24' (hours optional)
Returns a JSON summary of recent competitor prices for the SKU.
"""
    try:
        parts = {k.strip(): v.strip() for k, v in [p.split(":", 1) for p in text.split(";") if ":" in p]}
        sku = parts.get("sku")
        hours = int(parts.get("hours", "24"))
    except Exception as e:
        return json.dumps({"error": "bad input format; expected 'sku:SKU;hours:24'", "exception": str(e)})

    database = db.get_db(DB_NAME)
    coll = database.get_collection("competitor_prices")
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    docs = list(coll.find({"sku": sku, "timestamp": {"$gte": cutoff}}).sort("timestamp", -1).limit(100))

    prices = [d.get("price") for d in docs]
    if not prices:
        return json.dumps({"sku": sku, "count": 0, "prices": []})

    def _ts_to_iso(v):
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    summary = {
        "sku": sku,
        "count": len(prices),
        "min": min(prices),
        "max": max(prices),
        "avg": sum(prices) / len(prices),
        "samples": [{"price": d.get("price"), "source": d.get("source"), "timestamp": _ts_to_iso(d.get("timestamp"))} for d in docs[:10]]
    }
    return json.dumps(summary)


# Tool: get_demand_metrics
def get_demand_metrics_tool(text: str) -> str:
    """Expected input: 'sku:SKU-001;hours:24' (hours optional)
Returns aggregated demand metrics (views, units_sold) for the time window.
"""
    try:
        parts = {k.strip(): v.strip() for k, v in [p.split(":", 1) for p in text.split(";") if ":" in p]}
        sku = parts.get("sku")
        hours = int(parts.get("hours", "24"))
    except Exception as e:
        return json.dumps({"error": "bad input format; expected 'sku:SKU;hours:24'", "exception": str(e)})

    database = db.get_db(DB_NAME)
    coll = database.get_collection("demand_metrics")
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    pipeline = [
        {"$match": {"sku": sku, "timestamp": {"$gte": cutoff}}},
        {"$group": {"_id": "$sku", "views": {"$sum": "$views"}, "units_sold": {"$sum": "$units_sold"}, "count": {"$sum": 1}}}
    ]
    res = list(coll.aggregate(pipeline))
    if not res:
        return json.dumps({"sku": sku, "views": 0, "units_sold": 0, "count": 0})
    r = res[0]
    return json.dumps({"sku": sku, "views": r.get("views", 0), "units_sold": r.get("units_sold", 0), "count": r.get("count", 0)})


# Tool: get_margin_rules
def get_margin_rules_tool(text: str) -> str:
    """Expected input: 'sku:SKU-001' or 'sku:SKU-001;category:catA'
Returns the matching margin rule(s).
"""
    try:
        parts = {k.strip(): v.strip() for k, v in [p.split(":", 1) for p in text.split(";") if ":" in p]}
        sku = parts.get("sku")
        category = parts.get("category")
    except Exception as e:
        return json.dumps({"error": "bad input format; expected 'sku:SKU'", "exception": str(e)})

    database = db.get_db(DB_NAME)
    coll = database.get_collection("margin_rules")
    # Look for sku-specific rule, then category, then DEFAULT
    candidates = []
    if sku:
        r = coll.find_one({"sku_or_category": sku})
        if r:
            candidates.append(r)
    if category:
        r = coll.find_one({"sku_or_category": category})
        if r:
            candidates.append(r)
    r = coll.find_one({"sku_or_category": "DEFAULT"})
    if r:
        candidates.append(r)

    # Deduplicate ordering by priority
    seen = set()
    out = []
    for c in candidates:
        k = c.get("sku_or_category")
        if k in seen:
            continue
        seen.add(k)
        out.append(_serialize_doc(c))
    return json.dumps({"sku": sku, "rules": out})


# Tool: update_price (atomic write)
def update_price_tool(text: str) -> str:
    """Expected input: 'sku:SKU-001;price:17.99'
Performs an atomic find_one_and_update on products and returns the updated document.
"""
    try:
        parts = {k.strip(): v.strip() for k, v in [p.split(":", 1) for p in text.split(";") if ":" in p]}
        sku = parts.get("sku")
        price = float(parts.get("price"))
    except Exception as e:
        return json.dumps({"error": "bad input format; expected 'sku:SKU;price:9.99'", "exception": str(e)})

    database = db.get_db(DB_NAME)
    coll = database.get_collection("products")
    updated = coll.find_one_and_update(
        {"sku": sku},
        {"$set": {"price": price, "updated_at": datetime.utcnow()}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        return json.dumps({"error": "product not found", "sku": sku})
    # Serialize
    return json.dumps({"updated": _serialize_doc(updated)})
