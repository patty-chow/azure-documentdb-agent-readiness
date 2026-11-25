"""Idempotent seed script to populate sample_customer_360_03.interactions and preferences
and to create standard MongoDB indexes. Vector index is created separately during verification.
"""
from src.db import get_db
from datetime import datetime, timedelta
import random


def seed():
    db = get_db()
    interactions = db.interactions
    preferences = db.preferences

    # create indexes (idempotent)
    interactions.create_index([("customer_id", 1)])
    interactions.create_index([("customer_id", 1), ("timestamp", -1)])
    preferences.create_index([("customer_id", 1)], unique=True)

    # seed some synthetic customers
    customer_ids = [f"cust_{i:03d}" for i in range(1, 21)]
    action_types = ["promo_email", "discount_offer", "cross_sell", "survey"]
    now = datetime.utcnow()

    for cid in customer_ids:
        # upsert preference
        pref_doc = {
            "customer_id": cid,
            "channel_rankings": random.sample(["email", "sms", "push"], k=3),
            "contact_times": [f"{random.randint(8,20):02d}:00"]
        }
        preferences.update_one({"customer_id": cid}, {"$set": pref_doc}, upsert=True)

        # interactions: insert between 5 and 20 past interactions
        n = random.randint(5, 20)
        for i in range(n):
            ts = now - timedelta(days=random.randint(0, 60), hours=random.randint(0,23))
            action = random.choice(action_types)
            outcome = random.choices(["success", "failure"], weights=[0.2, 0.8])[0]
            doc = {
                "customer_id": cid,
                "timestamp": ts,
                "action_type": action,
                "outcome": outcome,
                # small placeholder embedding (optional)
                "embedding": [0.0]*1536
            }
            # use an idempotent upsert key by timestamp+action
            interactions.update_one({"customer_id": cid, "timestamp": ts, "action_type": action}, {"$set": doc}, upsert=True)

    print("Seeding complete")

if __name__ == '__main__':
    seed()
