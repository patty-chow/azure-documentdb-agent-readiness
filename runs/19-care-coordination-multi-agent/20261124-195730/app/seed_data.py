"""Seed script: upserts sample patients, referrals, medications and creates indexes.

This script connects to the cluster using DOCUMENTDB_URI and writes to sample_healthcare_19.
"""
from datetime import datetime
from app.db import get_db

SAMPLE_PATIENTS = [
    {
        "patient_id": "patient-001",
        "name": "Alice Example",
        "dob": "1980-05-01",
        "notes": "Patient presents for hypertension follow-up. Blood pressure elevated. Lifestyle counselling given.",
        "updated_at": datetime.utcnow()
    },
    {
        "patient_id": "patient-002",
        "name": "Bob Example",
        "dob": "1975-09-12",
        "notes": "Diabetes type 2. A1c stable. Consider endocrinology referral.",
        "updated_at": datetime.utcnow()
    }
]

SAMPLE_REFERRALS = [
    {
        "patient_id": "patient-002",
        "referral_id": "ref-001",
        "specialist": "Endocrinology",
        "note": "Please evaluate for refractory hyperglycemia. Consider insulin regimen review.",
        "created_at": datetime.utcnow()
    }
]

SAMPLE_MEDICATIONS = [
    {
        "patient_id": "patient-001",
        "medication": "Lisinopril 10mg",
        "dose": "10mg once daily",
        "updated_at": datetime.utcnow()
    },
    {
        "patient_id": "patient-002",
        "medication": "Metformin 500mg",
        "dose": "500mg twice daily",
        "updated_at": datetime.utcnow()
    }
]


def upsert_sample():
    db = get_db()
    # Ensure indexes
    print("Creating indexes on patient_id for patients/referrals/medications")
    db.patients.create_index("patient_id", unique=True)
    db.referrals.create_index("patient_id")
    db.medications.create_index("patient_id")

    for p in SAMPLE_PATIENTS:
        db.patients.update_one({"patient_id": p["patient_id"]}, {"$set": p}, upsert=True)
    for r in SAMPLE_REFERRALS:
        db.referrals.update_one({"referral_id": r["referral_id"]}, {"$set": r}, upsert=True)
    for m in SAMPLE_MEDICATIONS:
        db.medications.update_one({"patient_id": m["patient_id"], "medication": m["medication"]}, {"$set": m}, upsert=True)

    print("Seed data upsert complete.")

if __name__ == "__main__":
    upsert_sample()
