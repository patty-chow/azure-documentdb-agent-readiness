from datetime import datetime
from typing import Dict, List
from pymongo.collection import Collection


def compute_attribution_for_customer(events: List[Dict]) -> Dict[str, List[Dict]]:
    """Given a list of event documents (sorted by event_time asc), compute three attribution models.

    Returns a dict: { 'first-touch': [{channel, amount}], 'last-touch': [...], 'linear': [...] , 'total_revenue': n }
    """
    total_revenue = sum((e.get("revenue") or 0) for e in events)
    result = {"total_revenue": total_revenue}
    if not events:
        result.update({"first-touch": [], "last-touch": [], "linear": []})
        return result

    # First-touch
    first = events[0]
    first_channel = first.get("channel") or "unknown"
    result["first-touch"] = [{"channel": first_channel, "amount": total_revenue}]

    # Last-touch
    last = events[-1]
    last_channel = last.get("channel") or "unknown"
    result["last-touch"] = [{"channel": last_channel, "amount": total_revenue}]

    # Linear: split by touch counts per channel
    counts = {}
    for e in events:
        ch = e.get("channel") or "unknown"
        counts[ch] = counts.get(ch, 0) + 1
    total_touches = sum(counts.values())
    linear = []
    for ch, cnt in counts.items():
        share = (cnt / total_touches) if total_touches else 0
        linear.append({"channel": ch, "amount": total_revenue * share, "touches": cnt})
    result["linear"] = linear
    return result


def upsert_attribution_result(results_coll: Collection, customer_id: str, model_name: str, attribution: List[Dict], total_revenue: float):
    # determine next version
    last = results_coll.find({"customer_id": customer_id}).sort("version", -1).limit(1)
    last_list = list(last)
    last_version = last_list[0]["version"] if last_list else 0
    new_version = last_version + 1
    doc = {
        "customer_id": customer_id,
        "version": new_version,
        "model": model_name,
        "attribution": attribution,
        "total_revenue": total_revenue,
        "computed_at": datetime.utcnow(),
        "schemaVersion": 1,
    }
    results_coll.insert_one(doc)
    return doc


def run_attribution_for_all(db):
    events_coll = db["events"]
    results_coll = db["attribution_results"]

    # Ensure indexes exist (customer_id + event_time), and results index
    events_coll.create_index([("customer_id", 1), ("event_time", 1)])
    results_coll.create_index([("customer_id", 1), ("version", -1)])

    customer_ids = events_coll.distinct("customer_id")
    summary = {"processed": 0, "customers": []}
    for cid in customer_ids:
        events = list(events_coll.find({"customer_id": cid}).sort("event_time", 1))
        computed = compute_attribution_for_customer(events)
        # store three model variants
        for model in ["first-touch", "last-touch", "linear"]:
            attribution = computed.get(model, [])
            upsert_attribution_result(results_coll, cid, model, attribution, computed.get("total_revenue", 0))
        summary["processed"] += 1
        summary["customers"].append(cid)
    return summary
