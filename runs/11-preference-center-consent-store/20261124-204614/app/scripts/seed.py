"""Seed script to upsert sample consent documents and create TTL index.

Uses synchronous pymongo to avoid importing Motor in environments where motor/pymongo
versions may mismatch for this script. This is intentionally a small, idempotent script.

Usage: DOCUMENTDB_URI must be set in env or .env
"""
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
from pymongo import MongoClient

DB_NAME = "sample_customer_360_11"
DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
RETENTION_DAYS = int(os.getenv("CONSENT_RETENTION_DAYS", "365"))

SAMPLES = [
    {"customerId": "cust-001", "channels": {"email": True, "sms": False}},
    {"customerId": "cust-002", "channels": {"email": False, "sms": True}},
    {"customerId": "cust-003", "channels": {"email": True, "sms": True}},
]


def main():
    if not DOCUMENTDB_URI:
        raise RuntimeError("DOCUMENTDB_URI not set in environment")
    client = MongoClient(DOCUMENTDB_URI)
    db = client[DB_NAME]
    coll = db['consents']
    # create TTL index for expireAt semantics
    coll.create_index('retention_expires_at', expireAfterSeconds=0, name='ttl_retention_expires_at')

    now = datetime.utcnow()
    retention = now + timedelta(days=RETENTION_DAYS)
    for s in SAMPLES:
        doc = coll.find_one({'customerId': s['customerId']})
        if doc is None:
            doc = {
                'customerId': s['customerId'],
                'consentVersion': 1,
                'channels': s['channels'],
                'history': [
                    {
                        'timestamp': now,
                        'action': 'grant',
                        'channels': s['channels'],
                        'version': 1,
                        'actor': 'seed'
                    }
                ],
                'retention_expires_at': retention
            }
            coll.insert_one(doc)
            print(f"Inserted {s['customerId']}")
        else:
            coll.update_one({'customerId': s['customerId']}, {'$set': {'retention_expires_at': retention}})
            print(f"Updated retention for {s['customerId']}")

    docs = list(coll.find().limit(10))
    print("Sample documents in collection:")
    for d in docs:
        print(d)

if __name__ == '__main__':
    main()
