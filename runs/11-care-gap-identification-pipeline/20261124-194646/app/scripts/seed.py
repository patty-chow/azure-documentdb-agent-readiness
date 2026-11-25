"""Seed script for sample_healthcare_11.patients

This creates a small synthetic dataset of patients with dob, sex, diagnosis_codes, last_visit_date.
"""
import os
from datetime import datetime, timedelta, timezone
from random import randint, choice, seed
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
seed(42)

URI = os.environ.get("DOCUMENTDB_URI")
if not URI:
    raise RuntimeError("DOCUMENTDB_URI not set in environment. Copy .env.example to .env and fill in the connection string.")

client = MongoClient(URI)
db = client["sample_healthcare_11"]
coll = db["patients"]

# Idempotent: drop and recreate
print("Seeding sample_healthcare_11.patients ...")
coll.drop()

now = datetime.now(timezone.utc)

names = ["Alice Smith", "Bob Jones", "Carol Lee", "David Kim", "Eve Martinez", "Frank Zhao", "Grace Patel", "Hank Green", "Ivy Chen", "John Doe"]
sexes = ["F","M"]
diagnoses_pool = [[], ["diabetes"], ["hypertension"], ["diabetes","hypertension"], ["asthma"]]

patients = []
for i in range(1, 41):
    name = choice(names)
    sex = choice(sexes)
    # ages between 20 and 80
    age = randint(20,80)
    dob = (now - timedelta(days=365*age)).isoformat()
    diagnosis_codes = choice(diagnoses_pool)
    # last visit between 0 and 1500 days ago
    days_ago = randint(0, 1500)
    last_visit = (now - timedelta(days=days_ago)).isoformat()
    patient = {
        "patient_id": f"P{i:04d}",
        "name": name,
        "sex": sex,
        "dob": dob,
        "diagnosis_codes": diagnosis_codes,
        "last_visit_date": last_visit,
        "contact": {"phone": "555-010{}".format(i%10)}
    }
    patients.append(patient)

coll.insert_many(patients)
print(f"Inserted {len(patients)} patients")

# Create indexes recommended: patient_id unique, last_visit_date, diagnosis_codes (multikey)
print("Creating indexes...")
coll.create_index([("patient_id", 1)], unique=True)
coll.create_index([("last_visit_date", 1)])
coll.create_index([("diagnosis_codes", 1)])
print("Done.")
