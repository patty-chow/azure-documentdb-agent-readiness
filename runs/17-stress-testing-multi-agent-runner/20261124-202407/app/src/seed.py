"""Seed script: creates collections, indexes, and seed positions data (idempotent).
Run: python -m src.seed
"""
import os
import random
import time
from datetime import datetime
from src.db import get_db


def generate_position(i: int):
    instruments = ["BOND_US_10Y", "SWAP_EUR_5Y", "EQUITY_AAPL", "EQUITY_MSFT", "FX_USDJPY"]
    instrument = random.choice(instruments)
    account_id = f"acct_{random.randint(1,20)}"
    currency = random.choice(["USD", "EUR", "JPY"])
    quantity = round(random.uniform(1, 1000), 2)
    market_value = round(random.uniform(1000, 100000), 2)
    doc = {
        "_id": f"pos_{i}",
        "account_id": account_id,
        "instrument": instrument,
        "quantity": quantity,
        "market_value": market_value,
        "currency": currency,
        "risk_factors": {"rate": round(random.uniform(-0.05, 0.05), 6), "fx": 0},
        "created_at": int(time.time()),
    }
    return doc


def ensure_indexes(coll):
    # Create indexes useful for filtering/aggregation
    coll.create_index([("instrument", 1)], name="idx_instrument")
    coll.create_index([("account_id", 1)], name="idx_account")
    coll.create_index([("currency", 1)], name="idx_currency")
    coll.create_index([("risk_factors.rate", 1)], name="idx_rate")


def seed(n=100):
    db = get_db()
    positions = db.positions
    stress_runs = db.stress_runs

    ensure_indexes(positions)
    ensure_indexes(stress_runs)

    for i in range(1, n + 1):
        doc = generate_position(i)
        positions.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    print(f"Seeded {n} positions into {db.name}.positions")


if __name__ == "__main__":
    seed(100)
