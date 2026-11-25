"""Seed synthetic activity logs into the activity_logs collection.

Usage: python -m sample.seed
"""
import random
from datetime import datetime, timedelta
from sample.db import get_db

EVENT_TYPES = ["login", "file_access", "email_sent", "external_transfer", "privileged_command"]
NUM_EMPLOYEES = 60
DAYS = 30


def seed():
    db = get_db()
    coll = db["activity_logs"]
    # unique index to make upserts idempotent
    try:
        coll.create_index([("_id", 1)], unique=True)
    except Exception:
        pass

    base = datetime.utcnow()
    for emp in range(1, NUM_EMPLOYEES + 1):
        for day in range(DAYS):
            # random number of events per day
            events = random.randint(0, 6)
            for _ in range(events):
                ts = base - timedelta(days=day, hours=random.randint(0,23), minutes=random.randint(0,59))
                event_type = random.choice(EVENT_TYPES)
                doc_id = f"emp:{emp}:{ts.isoformat()}:{event_type}"
                doc = {
                    "_id": doc_id,
                    "employee_id": f"emp_{emp}",
                    "timestamp": ts,
                    "event_type": event_type,
                    "meta": {
                        "detail_score": random.random()
                    }
                }
                coll.replace_one({"_id": doc_id}, doc, upsert=True)
    print(f"Seeded sample activity_logs for {NUM_EMPLOYEES} employees over {DAYS} days")


if __name__ == "__main__":
    seed()
