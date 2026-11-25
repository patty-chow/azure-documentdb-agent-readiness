"""Seed script: loads sample incoming customer records into `incoming` collection.
Idempotent upsert by email.
"""
import json
from src.db import get_db

SAMPLE = [
    {"email": "alice@example.com", "name": "Alice Johnson", "addresses": [{"city": "Seattle"}]},
    {"email": "alice.j@example.com", "name": "A. Johnson", "addresses": [{"city": "Seattle"}]},
    {"email": "bob@example.com", "name": "Bob Smith", "addresses": [{"city": "Redmond"}]},
    {"email": "carol@example.com", "name": "Carol Lee", "addresses": [{"city": "Bellevue"}]},
]


def seed():
    db = get_db()
    incoming = db["incoming"]
    for doc in SAMPLE:
        email = doc["email"].lower()
        doc["email"] = email
        incoming.update_one({"email": email}, {"$set": doc}, upsert=True)
    print(f"Seeded {len(SAMPLE)} documents into 'incoming' collection")


if __name__ == "__main__":
    seed()
