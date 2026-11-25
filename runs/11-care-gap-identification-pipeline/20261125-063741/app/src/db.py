import os
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from dateutil import parser

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = "sample_healthcare_11"

if not DOCUMENTDB_URI:
    raise EnvironmentError("DOCUMENTDB_URI environment variable is required to run this sample.")

_client = None
_db = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(DOCUMENTDB_URI)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def ensure_indexes(verbose=True):
    db = get_db()
    # patients: diagnoses array index helps filtering by diagnosis
    p_idx = db.patients.create_index([("diagnoses", ASCENDING)], name="idx_patients_diagnoses")
    # visits: index on patient_id and visit_date for fast last-visit lookup
    v_idx = db.visits.create_index([("patient_id", ASCENDING), ("visit_date", ASCENDING)], name="idx_visits_patient_visitdate")
    if verbose:
        print(f"Ensured indexes: patients->{p_idx}, visits->{v_idx}")


def parse_date(d):
    if isinstance(d, datetime):
        return d
    if isinstance(d, str):
        return parser.parse(d)
    return None


def load_sample_data(overwrite=False, verbose=True):
    """Insert a small set of synthetic patients and visits. Idempotent: if patients exist, skip unless overwrite=True."""
    db = get_db()
    if db.patients.count_documents({}) > 0 and not overwrite:
        if verbose:
            print("Sample data already present; skipping insert. Use overwrite=True to force.")
        return
    # Clear existing small dataset
    db.patients.delete_many({})
    db.visits.delete_many({})

    patients = [
        {"_id": "p1", "name": "Alice Smith", "dob": "1970-05-15", "gender": "F", "diagnoses": ["hypertension"]},
        {"_id": "p2", "name": "Bob Jones", "dob": "1955-02-20", "gender": "M", "diagnoses": ["diabetes"]},
        {"_id": "p3", "name": "Carol White", "dob": "1985-11-30", "gender": "F", "diagnoses": []},
        {"_id": "p4", "name": "Dan Black", "dob": "1948-08-01", "gender": "M", "diagnoses": ["diabetes","hyperlipidemia"]},
        {"_id": "p5", "name": "Eve Green", "dob": "1990-01-10", "gender": "F", "diagnoses": ["asthma"]},
    ]
    db.patients.insert_many(patients)

    visits = [
        {"patient_id": "p1", "visit_date": parser.parse("2022-01-10")},
        {"patient_id": "p2", "visit_date": parser.parse("2017-06-20")},
        {"patient_id": "p3", "visit_date": parser.parse("2024-02-15")},
        {"patient_id": "p4", "visit_date": parser.parse("2015-09-01")},
        # p5 no visits
    ]
    db.visits.insert_many(visits)
    ensure_indexes(verbose=verbose)
    if verbose:
        print("Inserted sample patients and visits.")


def get_all_patients_with_last_visit():
    db = get_db()
    # For each patient, find the most recent visit from visits collection
    patients = list(db.patients.find({}))
    # Build a map of last visit per patient
    last_visits = {}
    cursor = db.visits.aggregate([
        {"$sort": {"visit_date": -1}},
        {"$group": {"_id": "$patient_id", "last_visit": {"$first": "$visit_date"}}}
    ])
    for doc in cursor:
        last_visits[doc["_id"]] = doc["last_visit"]

    results = []
    for p in patients:
        p_copy = dict(p)
        lv = last_visits.get(p["_id"]) if last_visits else None
        p_copy["last_visit_date"] = lv
        # compute age
        dob = parse_date(p.get("dob"))
        if dob:
            today = datetime.utcnow()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            p_copy["age"] = age
        results.append(p_copy)
    return results
