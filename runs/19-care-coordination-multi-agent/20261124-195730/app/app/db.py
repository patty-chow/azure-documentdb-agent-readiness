import os
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection

# Load .env if present (do not commit .env)
load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DB_NAME = os.environ.get("DOCUMENTDB_DB", "sample_healthcare_19")

if DOCUMENTDB_URI is None:
    # Defer raising until connection is attempted; allow tests to import module without env var
    DOCUMENTDB_URI = None

# Singleton MongoClient pattern (documentdb-driver guidance)
_client: MongoClient | None = None
_client_connect_promise = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not DOCUMENTDB_URI:
            raise RuntimeError("DOCUMENTDB_URI environment variable is not set")
        _client = MongoClient(DOCUMENTDB_URI)
        # connect lazily
    return _client


def get_db():
    client = get_client()
    return client[DB_NAME]


def get_collection(name: str) -> Collection:
    return get_db()[name]


def ensure_indexes():
    """Ensure single-field indexes used by the sample. Idempotent."""
    db = get_db()
    # Single-field indexes for sample query patterns
    db["patients"].create_index([("patient_id", 1)], name="idx_patient_id")
    db["referrals"].create_index([("patient_id", 1)], name="idx_referrals_patient_id")
    db["medications"].create_index([("patient_id", 1)], name="idx_medications_patient_id")


def insert_care_plan(plan: dict[str, Any]) -> Any:
    col = get_collection("care_plans")
    res = col.insert_one(plan)
    return res.inserted_id


# Helper for demos to produce a care plan document
def make_care_plan_doc(patient_id: str, plan_text: str, sources: list[dict]) -> dict:
    return {
        "patient_id": patient_id,
        "created_at": datetime.utcnow(),
        "plan_text": plan_text,
        "sources": sources,
    }
