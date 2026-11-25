"""AML analysis functions: run aggregation pipelines to detect suspicious chains and produce structured narratives."""
from datetime import datetime, timedelta
from .db import get_db


def detect_structuring(min_amount_threshold=1000, per_tx_threshold=1000, min_count=3, window_hours=24):
    db = get_db()
    tx = db.transactions
    window_start = (datetime.utcnow() - timedelta(hours=window_hours)).isoformat()
    # Find accounts receiving >= min_count transactions in window where each tx < per_tx_threshold
    pipeline = [
        {"$match": {"timestamp": {"$gte": window_start}, "amount": {"$lt": per_tx_threshold}}},
        {"$group": {"_id": "$to_account", "count": {"$sum": 1}, "total": {"$sum": "$amount"}, "tx_ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gte": min_count}}},
        {"$project": {"account": "$_id", "count": 1, "total": 1, "tx_ids": 1, "_id": 0}}
    ]
    return list(tx.aggregate(pipeline))


def detect_rapid_pass_through(min_amount=10000, min_hops=2, max_minutes=30):
    db = get_db()
    tx = db.transactions
    # Heuristic: find chains of length >= min_hops where timestamps are within max_minutes from first to last
    # We'll use $graphLookup on from_account->to_account by treating accounts as nodes via transactions collection
    # Start from transactions with amount >= min_amount
    pipeline = [
        {"$match": {"amount": {"$gte": min_amount}}},
        {"$project": {"_id": 1, "from_account": 1, "to_account": 1, "amount": 1, "timestamp": 1}},
    ]
    results = []
    for doc in tx.aggregate(pipeline):
        # graphLookup: find downstream transactions starting from this to_account
        graph = list(tx.aggregate([
            {"$match": {"from_account": doc["to_account"]}},
            {"$graphLookup": {
                "from": "transactions",
                "startWith": "$to_account",
                "connectFromField": "to_account",
                "connectToField": "from_account",
                "maxDepth": min_hops + 2,
                "depthField": "depth",
                "as": "chain"
            }},
            {"$limit": 1}
        ]))
        if graph and graph[0].get("chain"):
            # crude time check
            timestamps = [doc["timestamp"]]
            for c in graph[0]["chain"]:
                timestamps.append(c.get("timestamp"))
            try:
                t0 = datetime.fromisoformat(timestamps[0])
                tlast = datetime.fromisoformat(timestamps[-1])
                if (tlast - t0).total_seconds() <= max_minutes * 60:
                    results.append({"start_tx": doc["_id"], "chain_length": len(graph[0]["chain"])+1, "start_ts": timestamps[0], "end_ts": timestamps[-1]})
            except Exception:
                continue
    return results


def detect_circular_transfers(max_cycle_length=6):
    db = get_db()
    tx = db.transactions
    # For each account, do graphLookup and see if it reaches back to the start account
    accounts = set()
    for d in tx.find({}, {"from_account": 1, "to_account": 1}):
        if d.get("from_account"): accounts.add(d.get("from_account"))
        if d.get("to_account"): accounts.add(d.get("to_account"))
    results = []
    for acc in accounts:
        pipeline = [
            {"$match": {"from_account": acc}},
            {"$graphLookup": {
                "from": "transactions",
                "startWith": "$to_account",
                "connectFromField": "to_account",
                "connectToField": "from_account",
                "maxDepth": max_cycle_length,
                "depthField": "depth",
                "as": "paths"
            }},
            {"$project": {"paths.to_account": 1, "paths.from_account":1}}
        ]
        docs = list(tx.aggregate(pipeline))
        for d in docs:
            for p in d.get("paths", []):
                if p.get("to_account") == acc:
                    results.append({"start_account": acc, "path_from": p.get("from_account"), "path_to": p.get("to_account")})
    return results


def summarize_flags(flags, use_llm=False, llm_client=None):
    narratives = []
    for ftype, items in flags.items():
        for itm in items:
            if use_llm and llm_client:
                # In sample we treat llm_client as a callable that returns text
                text = llm_client(ftype, itm)
            else:
                text = {
                    "type": ftype,
                    "details": itm,
                    "narrative": f"Flagged {ftype} with details: {itm}"
                }
            narratives.append(text)
    return narratives


def analyze(use_llm=False, llm_client=None):
    flags = {}
    struct = detect_structuring()
    if struct:
        flags["structuring"] = struct
    rapid = detect_rapid_pass_through()
    if rapid:
        flags["rapid_pass_through"] = rapid
    circ = detect_circular_transfers()
    if circ:
        flags["circular"] = circ
    return summarize_flags(flags, use_llm=use_llm, llm_client=llm_client)
