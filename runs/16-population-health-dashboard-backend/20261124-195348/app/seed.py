import argparse
import random
import uuid
from datetime import datetime
from db import get_db

GENDERS = ["female", "male", "other"]
REGIONS = ["North", "South", "East", "West", "Central"]
DIAGNOSES = ["HTN", "DM", "ASTHMA", "COPD", "CKD", "CAD", "DEP", "ANX", "OBESE"]


def gen_patient(i: int):
    patient_id = f"patient-{i:06d}"
    age = random.randint(0, 100)
    gender = random.choice(GENDERS)
    region = random.choice(REGIONS)
    # each patient has 1-3 diagnoses
    diagnoses = random.sample(DIAGNOSES, k=random.randint(1, 3))
    doc = {
        "patient_id": patient_id,
        "age": age,
        "gender": gender,
        "region": region,
        "diagnoses": diagnoses,
        "lastEncounterDate": datetime.utcnow(),
    }
    return doc


def main(count: int = 5000):
    db = get_db()
    patients = db.patients
    # ensure indexes expected by sample
    patients.create_index([("patient_id", 1)], unique=True)
    patients.create_index([("diagnoses", 1)])
    patients.create_index([("gender", 1)])
    patients.create_index([("region", 1)])
    patients.create_index([("age", 1)])

    ops = []
    for i in range(1, count + 1):
        doc = gen_patient(i)
        # upsert by patient_id for idempotency
        patients.update_one({"patient_id": doc["patient_id"]}, {"$set": doc}, upsert=True)
        if i % 500 == 0:
            print(f"Inserted/upserted {i} patients")

    print("Seeding complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    args = parser.parse_args()
    main(args.count)
