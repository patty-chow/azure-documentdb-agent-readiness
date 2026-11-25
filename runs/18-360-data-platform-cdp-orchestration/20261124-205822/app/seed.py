import json
from src.db import get_database

SAMPLE = [
    {"name": "Alice Smith", "email": "alice@example.com", "addresses": [{"line1": "1 Main St", "city": "Metropolis"}]},
    {"name": "Alicia Smith", "email": "alice@example.com", "addresses": [{"line1": "1 Main St", "city": "Metropolis"}]},
    {"name": "Bob Jones", "email": "bob.jones@startup.io", "addresses": [{"line1": "42 Startup Way", "city": "Innovation"}]},
    {"name": "Robert Jones", "email": "robert@startup.io", "addresses": [{"line1": "42 Startup Way", "city": "Innovation"}]},
    {"name": "Carol", "email": "carol@acme.org"}
]


def seed():
    db = get_database()
    customers = db.get_collection("customers")
    for r in SAMPLE:
        customers.update_one({"email": r.get("email")}, {"$set": r}, upsert=True)
    print(f"Seeded {len(SAMPLE)} records into {db.name}.customers")


if __name__ == '__main__':
    seed()
