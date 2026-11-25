from datetime import datetime
from typing import List, Optional, Dict, Any
from .db import get_db


def outcomes_pipeline(strategy_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
    match = {"type": "outcome", "strategy_id": strategy_id}
    if start or end:
        tsq = {}
        if start:
            tsq.setdefault("$gte", start)
        if end:
            tsq.setdefault("$lte", end)
        match["timestamp"] = tsq

    pipeline = [
        {"$match": match},
        {"$sort": {"timestamp": 1}},
        # project only needed fields
        {"$project": {"timestamp": 1, "pnl": 1, "_id": 0}},
    ]
    return pipeline


def stats_for_strategy(strategy_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Dict[str, Any]:
    db = get_db()
    coll = db["journal"]
    # Basic aggregates computed server-side
    group_pipeline = []
    match = {"type": "outcome", "strategy_id": strategy_id}
    if start or end:
        tsq = {}
        if start:
            tsq.setdefault("$gte", start)
        if end:
            tsq.setdefault("$lte", end)
        match["timestamp"] = tsq

    group_pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "trade_count": {"$sum": 1},
                "total_pnl": {"$sum": "$pnl"},
                "avg_pnl": {"$avg": "$pnl"},
                "wins": {"$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}},
            }
        },
        {"$project": {"_id": 0, "trade_count": 1, "total_pnl": 1, "avg_pnl": 1, "wins": 1}},
    ]

    agg = list(coll.aggregate(group_pipeline))
    base = agg[0] if agg else {"trade_count": 0, "total_pnl": 0.0, "avg_pnl": 0.0, "wins": 0}

    # For max drawdown, retrieve ordered series and compute client-side
    series = list(coll.aggregate(outcomes_pipeline(strategy_id, start, end)))
    # compute cumulative pnl series
    cumul = []
    running = 0.0
    for doc in series:
        running += float(doc.get("pnl", 0.0))
        cumul.append({"timestamp": doc["timestamp"], "cumulative": running})

    max_drawdown = 0.0
    peak = None
    for point in cumul:
        if peak is None or point["cumulative"] > peak:
            peak = point["cumulative"]
        dd = peak - point["cumulative"]
        if dd > max_drawdown:
            max_drawdown = dd

    win_rate = (base["wins"] / base["trade_count"]) if base["trade_count"] else 0.0

    return {
        "strategy_id": strategy_id,
        "trade_count": int(base.get("trade_count", 0)),
        "total_pnl": float(base.get("total_pnl", 0.0)),
        "avg_pnl": float(base.get("avg_pnl") or 0.0),
        "win_rate": float(win_rate),
        "max_drawdown": float(max_drawdown),
        "cumulative_series": cumul,
    }
