import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DOCUMENTDB_DB", "sample_healthcare_11")

_client = None

def get_client():
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable is required")
        _client = MongoClient(DOCUMENTDB_URI, serverSelectionTimeoutMS=5000)
        try:
            _client.server_info()
        except ServerSelectionTimeoutError as e:
            raise RuntimeError(f"Could not connect to DocumentDB cluster: {e}")
    return _client


def get_db():
    return get_client()[DATABASE_NAME]


def ensure_indexes(db):
    # patients: patient_id (unique), dob, diagnosis_codes (multikey)
    patients = db.get_collection("patients")
    patients.create_index([("patient_id", 1)], unique=True)
    patients.create_index([("dob", 1)])
    patients.create_index([("diagnosis_codes", 1)])

    # visits: patient_id, visit_date (descending for fast last-visit lookup)
    visits = db.get_collection("visits")
    visits.create_index([("patient_id", 1), ("visit_date", -1)])

    print("Indexes ensured on patients and visits collections")
