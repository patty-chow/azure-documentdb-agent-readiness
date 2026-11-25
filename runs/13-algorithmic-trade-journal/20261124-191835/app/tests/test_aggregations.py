import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_db, ensure_indexes
from app.aggregations import stats_for_strategy
from datetime import datetime, timedelta

def test_stats_sequence():
    ensure_indexes()
    db = get_db()
    coll = db["journal"]
    # create deterministic small dataset for test-strat
    strat = "test_strat"
    # clear prior test data
    coll.delete_many({"strategy_id": strat})
    now = datetime.utcnow()
    pnls = [1.0, -0.5, 2.0, -1.0]
    for i, p in enumerate(pnls):
        coll.insert_one({"strategy_id": strat, "timestamp": now + timedelta(minutes=i), "type": "outcome", "pnl": p})

    stats = stats_for_strategy(strat)
    assert stats["trade_count"] == len(pnls)
    assert abs(stats["total_pnl"] - sum(pnls)) < 1e-6
    assert abs(stats["avg_pnl"] - (sum(pnls)/len(pnls))) < 1e-6
    assert stats["win_rate"] == 0.5
    # cumulative series should be len 4
    assert len(stats["cumulative_series"]) == 4
    # max drawdown: after cum series [1.0,0.5,2.5,1.5] peak 2.5 trough 1.5 -> drawdown 1.0
    assert abs(stats["max_drawdown"] - 1.0) < 1e-6
