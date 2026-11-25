"""Seed script: creates sample patients and visits into sample_healthcare_11 database.

Run: python src/seed.py
"""
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker
from tqdm import tqdm

from db import get_db, ensure_indexes

fake = Faker()

NUM_PATIENTS = 120

SCREENING_DIAGNOSIS_CODES = {
    "diabetes": "E11",  # ICD-10 code sample
}

AGE_DISTRIBUTION = [25, 35, 45, 55, 65, 75]


def random_dob(age):
    today = datetime.utcnow().date()
    birth_year = today.year - age
    # randomize within the year
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(birth_year, month, day)


def seed():
    db = get_db()
    ensure_indexes(db)

    patients = db.get_collection("patients")
    visits = db.get_collection("visits")

    patients.delete_many({})
    visits.delete_many({})

    patient_docs = []
    visit_docs = []

    for i in range(NUM_PATIENTS):
        pid = f"P{i:04d}"
        age = random.choice(AGE_DISTRIBUTION)
        dob = random_dob(age)
        gender = random.choice(["F", "M"])
        # randomly assign diabetes diagnosis to some older patients
        diagnoses = []
        if random.random() < 0.15:
            diagnoses.append(SCREENING_DIAGNOSIS_CODES["diabetes"])
        contact = {"email": fake.email(), "phone": fake.phone_number()}

        patient_docs.append({
            "patient_id": pid,
            "dob": dob,
            "gender": gender,
            "diagnosis_codes": diagnoses,
            "contact": contact,
        })

        # create 0-5 visits over the past 5 years
        num_visits = random.choice([0, 1, 2, 3, 4])
        for v in range(num_visits):
            days_ago = random.randint(0, 5 * 365)
            visit_date = datetime.utcnow() - timedelta(days=days_ago)
            visit_type = random.choice(["wellness", "lab", "specialty"])
            visit_docs.append({
                "patient_id": pid,
                "visit_date": visit_date,
                "visit_type": visit_type,
            })

    print(f"Inserting {len(patient_docs)} patients and {len(visit_docs)} visits...")
    if patient_docs:
        patients.insert_many(patient_docs)
    if visit_docs:
        visits.insert_many(visit_docs)

    print("Seed complete")


if __name__ == "__main__":
    seed()
