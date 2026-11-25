"""Idempotent seed script for positions collection.
Upserts documents by position_id so it can be run multiple times.
"""
import os
import random
from datetime import datetime, timedelta
from uuid import uuid4

from pymongo import UpdateOne

from src.db import get_positions_collection


def random_maturity(from_years: int, to_years: int) -> datetime:
    now = datetime.utcnow()
    years = random.uniform(from_years, to_years)
    days = int(years * 365)
    return now + timedelta(days=days)


def generate_sample_positions(n=60):
    positions = []
    for i in range(n):
        rate_type = random.choice(["fixed", "floating"])
        if i < n * 0.2:
            # short
            maturity = random_maturity(0.1, 1)
        elif i < n * 0.45:
            maturity = random_maturity(1, 3)
        elif i < n * 0.7:
            maturity = random_maturity(3, 5)
        elif i < n * 0.9:
            maturity = random_maturity(5, 10)
        else:
            maturity = random_maturity(10, 30)

        pos = {
            "position_id": f"pos-{i+1}",
            "notional": round(random.uniform(1e5, 5e7), 2),
            "currency": "USD",
            "rate_type": rate_type,
            "coupon_rate": round(random.uniform(0.0, 0.08) if rate_type == "fixed" else random.uniform(0.0, 0.05), 4),
            "start_date": datetime.utcnow(),
            "maturity_date": maturity,
            "repricing_frequency": "1Y" if rate_type == "floating" else None,
            "accrual_basis": 365,
        }
        positions.append(pos)
    return positions


def seed(n=60):
    coll = get_positions_collection()
    positions = generate_sample_positions(n)
    ops = []
    for p in positions:
        ops.append(
            UpdateOne({"position_id": p["position_id"]}, {"$set": p}, upsert=True)
        )
    if ops:
        res = coll.bulk_write(ops)
        print("Seed completed.", res.bulk_api_result)


if __name__ == "__main__":
    seed()
