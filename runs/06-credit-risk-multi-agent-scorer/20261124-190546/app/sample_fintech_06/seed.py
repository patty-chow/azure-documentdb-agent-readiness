"""Idempotent seed script to create the applicants collection and insert sample docs."""
from .db import get_db

SAMPLE = [
    {
        "_id": "applicant-1",
        "schemaVersion": 1,
        "name": "Alice Example",
        "income": 120000,
        "debts": 10000,
        "transactions": [
            {"date": "2023-01-01", "amount": -50, "merchant": "Coffee"},
            {"date": "2023-03-15", "amount": 2000, "merchant": "Payroll"},
        ],
        "pastLoans": [{"amount": 10000, "status": "paid"}],
    },
    {
        "_id": "applicant-2",
        "schemaVersion": 1,
        "name": "Bob Sample",
        "income": 40000,
        "debts": 30000,
        "transactions": [
            {"date": "2023-02-10", "amount": -500, "merchant": "Electronics"},
        ],
        "pastLoans": [{"amount": 5000, "status": "default"}],
    },
]


def main():
    db = get_db()
    coll = db.applicants
    for doc in SAMPLE:
        coll.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    print(f"Seeded {len(SAMPLE)} applicants")


if __name__ == "__main__":
    main()
