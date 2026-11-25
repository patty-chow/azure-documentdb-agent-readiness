"""Seed sample data into the DocumentDB cluster used by this sample.

Idempotent: uses upsert semantics to avoid duplicates. Also ensures single-field indexes.
"""
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

from app.db import get_collection, ensure_indexes

# Sample documents
PATIENTS = [
    {
        "patient_id": "patient-001",
        "name": "Alice Example",
        "timestamp": datetime(2024, 1, 1),
        "note": "47-year-old with hypertension. Blood pressure elevated at last visit. Follow up in 2 weeks.",
    },
    {
        "patient_id": "patient-002",
        "name": "Bob Example",
        "timestamp": datetime(2024, 2, 14),
        "note": "65-year-old with type 2 diabetes. HbA1c 8.2%. Consider med review.",
    },
]

REFERRALS = [
    {
        "patient_id": "patient-001",
        "referrer": "Dr. GP",
        "timestamp": datetime(2024, 3, 1),
        "note": "Referral to cardiology for evaluation of hypertension and chest pain.",
    }
]

MEDICATIONS = [
    {
        "patient_id": "patient-001",
        "medication": "Lisinopril 10mg",
        "effective_date": datetime(2024, 1, 2),
    },
    {
        "patient_id": "patient-002",
        "medication": "Metformin 500mg",
        "effective_date": datetime(2024, 2, 15),
    },
]


def upsert_many(col_name: str, docs: list):
    col = get_collection(col_name)
    for d in docs:
        filter = {"patient_id": d["patient_id"]}
        # Use timestamp/effective_date to distinguish multiple docs per patient
        # If the exact doc exists, replace; otherwise insert with an appended _seed_id
        col.update_one({**filter, **{"note": d.get("note"), "medication": d.get("medication")}}, {"$set": d}, upsert=True)


def main():
    ensure_indexes()
    upsert_many("patients", PATIENTS)
    upsert_many("referrals", REFERRALS)
    upsert_many("medications", MEDICATIONS)
    print("Seed complete. Collections: patients, referrals, medications. DB:", os.environ.get("DOCUMENTDB_DB", "sample_healthcare_19"))


if __name__ == "__main__":
    main()
