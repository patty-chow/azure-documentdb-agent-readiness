"""
Idempotent seed script to create sample data for two strategies.
Run: python scripts/seed_data.py
"""
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path

# Ensure project root is on path when script is run directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_db, ensure_indexes
from app.journal import Signal, Execution, Outcome, insert_signal, insert_execution, insert_outcome


def seed():
    ensure_indexes()
    now = datetime.utcnow()
    strategies = ["strat_A", "strat_B"]
    db = get_db()
    coll = db["journal"]

    # Check if data already present for strategies (idempotent guard)
    existing = coll.count_documents({"type": "outcome", "strategy_id": {"$in": strategies}})
    if existing >= 10:
        print("Seed appears already applied; exiting")
        return

    for strat in strategies:
        # create a few signals/executions/outcomes across a timespan
        cumulative = 0.0
        for i in range(10):
            t = now - timedelta(days=10 - i)
            s = Signal(strategy_id=strat, timestamp=t, signal_type=random.choice(["long","short"]))
            insert_signal(s)
            e = Execution(strategy_id=strat, timestamp=t, side=s.signal_type, price=100+random.random(), quantity=1)
            insert_execution(e)
            # outcome: random pnl with slight positive bias for strat_A
            bias = 0.5 if strat == "strat_A" else 0.0
            pnl = round(random.uniform(-2, 3) + bias, 2)
            cumulative += pnl
            o = Outcome(strategy_id=strat, timestamp=t, pnl=pnl)
            insert_outcome(o)
    print("Seed complete")

if __name__ == "__main__":
    seed()
