"""Idempotent seed script for customers and events used by the cohort sample.

Usage: python scripts/seed.py
Reads DOCUMENTDB_URI and DB_NAME from environment (.env supported)
"""
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv
from pymongo import ASCENDING

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB_NAME = os.getenv("DB_NAME", "sample_customer_360_15")

if not DOCUMENTDB_URI:
    raise RuntimeError("Set DOCUMENTDB_URI in environment or .env file")

from pymongo import MongoClient
client = MongoClient(DOCUMENTDB_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

customers = db.customers
events = db.events

print("Seeding sample data into database:", DB_NAME)

# For demo: 800 customers over last 12 months
NUM_CUSTOMERS = 800
months_back = 12
now = datetime.utcnow()
start_month = datetime(now.year, now.month, 1) - timedelta(days=30*months_back)

# wipe collections (idempotent seed runtime). For a demo we delete and reinsert.
customers.drop()
events.drop()

customer_docs = []
for i in range(NUM_CUSTOMERS):
    # distribute acquisition over the last 12 months
    age_days = random.randint(0, months_back * 30)
    acquired_at = now - timedelta(days=age_days)
    customer_id = f"CUST-{i:05d}"
    channel = random.choice(["organic", "ads", "referral", "email"])
    primary_product_id = random.choice(["prod-A", "prod-B", "prod-C"])
    customer_docs.append({
        "customer_id": customer_id,
        "acquired_at": acquired_at,
        "channel": channel,
        "primary_product_id": primary_product_id,
        "schemaVersion": 1
    })

if customer_docs:
    customers.insert_many(customer_docs)

# events: for each customer, generate 0-5 post-acquisition events within 180 days
event_docs = []
for c in customer_docs:
    num_events = random.choices([0,1,2,3,4], weights=[0.2,0.4,0.2,0.15,0.05])[0]
    for k in range(num_events):
        # event days after acquisition
        d = random.randint(0, 180)
        event_date = c['acquired_at'] + timedelta(days=d)
        event_docs.append({
            "customer_id": c['customer_id'],
            "event_date": event_date,
            "event_type": random.choice(["purchase", "login", "view"]),
            "product_id": c['primary_product_id'],
            "amount": random.choice([10, 20, 50, 100])
        })

if event_docs:
    events.insert_many(event_docs)

# create helpful indexes
customers.create_index([("customer_id", ASCENDING)], unique=True)
customers.create_index([("acquired_at", ASCENDING)])
customers.create_index([("channel", ASCENDING)])
customers.create_index([("primary_product_id", ASCENDING)])

events.create_index([("customer_id", ASCENDING)])
events.create_index([("event_date", ASCENDING)])
events.create_index([("product_id", ASCENDING)])

print("Seed completed: customers=", customers.count_documents({}), "events=", events.count_documents({}))
