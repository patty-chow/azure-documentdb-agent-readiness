import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from pymongo import ASCENDING, DESCENDING
from dotenv import load_dotenv

from src.db import get_db

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Simple deterministic rule engine for segmentation (fallback when no LLM key present)
SEGMENTATION_RULES = {
    "high_activity": {"recency_days": 30, "frequency": 10},
    "active": {"recency_days": 90, "frequency": 3},
}


def compute_metrics(customer_id: str) -> Dict[str, Any]:
    """Run an aggregation pipeline to compute recency (days since last event),
    frequency (count in a recent window), and category affinity (counts and top category ratio).
    Returns a dict with metrics.
    """
    db = get_db()
    events = db.events

    now = datetime.now(timezone.utc)

    pipeline = [
        {"$match": {"customer_id": customer_id}},
        {"$group": {
            "_id": "$customer_id",
            "lastSeen": {"$max": "$timestamp"},
            "total": {"$sum": 1},
            "byCategory": {"$push": "$category"}
        }},
        {"$project": {
            "_id": 0,
            "customer_id": "$_id",
            "lastSeen": 1,
            "total": 1,
            "byCategory": 1
        }}
    ]

    res = list(events.aggregate(pipeline))
    if not res:
        # no events
        return {"customer_id": customer_id, "lastSeen": None, "recency_days": None, "total": 0, "category_counts": {}, "top_category": None, "top_category_ratio": 0.0}

    doc = res[0]
    last_seen = doc.get("lastSeen")
    if last_seen is None:
        recency_days = None
    else:
        # ensure timezone-aware
        if last_seen.tzinfo is None:
            # assume UTC
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        recency_days = (now - last_seen).days

    # frequency in last 30 days
    window_start = now - timedelta(days=30)
    freq_pipeline = [
        {"$match": {"customer_id": customer_id, "timestamp": {"$gte": window_start}}},
        {"$count": "count"}
    ]
    freq_res = list(events.aggregate(freq_pipeline))
    freq = freq_res[0]["count"] if freq_res else 0

    # category affinity
    cats = doc.get("byCategory", [])
    counts = {}
    for c in cats:
        counts[c] = counts.get(c, 0) + 1
    top_category = None
    top_ratio = 0.0
    if counts:
        top_category = max(counts.items(), key=lambda kv: kv[1])[0]
        top_ratio = counts[top_category] / sum(counts.values())

    return {
        "customer_id": customer_id,
        "lastSeen": last_seen,
        "recency_days": recency_days,
        "total": doc.get("total", 0),
        "frequency_30d": freq,
        "category_counts": counts,
        "top_category": top_category,
        "top_category_ratio": top_ratio,
    }


def assign_segment_from_rules(metrics: Dict[str, Any]) -> str:
    """Deterministic rules-based assignment used when no LLM is configured."""
    recency = metrics.get("recency_days")
    freq = metrics.get("frequency_30d", 0)
    top_ratio = metrics.get("top_category_ratio", 0.0)
    top_category = metrics.get("top_category")

    if recency is None:
        return "NoActivity"

    if recency <= SEGMENTATION_RULES["high_activity"]["recency_days"] and freq >= SEGMENTATION_RULES["high_activity"]["frequency"]:
        seg = "Active-High"
    elif recency <= SEGMENTATION_RULES["active"]["recency_days"] and freq >= SEGMENTATION_RULES["active"]["frequency"]:
        seg = "Active"
    else:
        seg = "Inactive"

    # if top category dominating, append category tag
    if top_category and top_ratio >= 0.6:
        seg = f"{seg}-LoyalTo-{top_category}"

    return seg


def run_agent_assign_segment(customer_id: str, use_llm: bool = False) -> Dict[str, Any]:
    """Compute metrics, ask LLM (optionally) to assign a segment, and write back to profile.

    If use_llm is False or OPENAI_API_KEY not present, uses deterministic rules.
    Returns the updated customer profile document.
    """
    db = get_db()
    customers = db.customers

    metrics = compute_metrics(customer_id)

    label = None
    if use_llm and OPENAI_KEY:
        try:
            # Import langchain/OpenAI lazily to avoid import-time issues when it's unavailable or incompatible
            from langchain import OpenAI
            prompt = f"""
You are a segmentation assistant. Given the customer behavioural metrics in JSON, return a single short segment label.
Metrics: {metrics}
Rules: If recency_days <= 30 and frequency_30d >= 10 -> Active-High. Else if recency_days <= 90 and frequency_30d >=3 -> Active. Else Inactive. If top_category_ratio >= 0.6 append '-LoyalTo-<category>'.
Return only the label string.
"""
            llm = OpenAI(openai_api_key=OPENAI_KEY, temperature=0)
            label = llm(prompt).strip()
        except Exception:
            # Fall back to deterministic if any import or runtime issue
            label = assign_segment_from_rules(metrics)
    else:
        label = assign_segment_from_rules(metrics)

    # write back to customer profile
    update = {"segment": label, "lastSegmentedAt": datetime.utcnow(), "schemaVersion": 1}
    customers.update_one({"customer_id": customer_id}, {"$set": update}, upsert=True)

    profile = customers.find_one({"customer_id": customer_id})
    return {"profile": profile, "metrics": metrics, "assigned_segment": label}
