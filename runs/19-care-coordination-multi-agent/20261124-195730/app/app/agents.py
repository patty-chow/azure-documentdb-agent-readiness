from typing import List, Dict, Any
from .db import get_db
from datetime import datetime


def get_patient_record(patient_id: str) -> Dict[str, Any]:
    db = get_db()
    doc = db.patients.find_one({"patient_id": patient_id})
    return doc or {}


def get_referrals(patient_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.referrals.find({"patient_id": patient_id}).sort("created_at", -1)
    return list(cursor)


def get_medications(patient_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.medications.find({"patient_id": patient_id}).sort("updated_at", -1)
    return list(cursor)


def write_care_plan(patient_id: str, care_plan: Dict[str, Any]) -> str:
    db = get_db()
    doc = {
        "patient_id": patient_id,
        "care_plan": care_plan,
        "created_at": datetime.utcnow()
    }
    res = db.care_plans.insert_one(doc)
    return str(res.inserted_id)
