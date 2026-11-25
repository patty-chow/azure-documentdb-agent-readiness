from typing import Any, Dict, List
from .db import get_collection

class GPAgent:
    """Primary care agent: reads primary care notes for a patient."""
    def fetch(self, patient_id: str) -> Dict[str, Any]:
        col = get_collection("patients")
        docs = list(col.find({"patient_id": patient_id}).sort("timestamp", -1))
        # Return combined text and metadata
        notes = "\n\n".join(d.get("note", "") for d in docs)
        return {"patient_id": patient_id, "notes": notes, "records": docs}

class SpecialistAgent:
    """Referral agent: retrieves referral notes for a patient."""
    def fetch(self, patient_id: str) -> Dict[str, Any]:
        col = get_collection("referrals")
        docs = list(col.find({"patient_id": patient_id}).sort("timestamp", -1))
        notes = "\n\n".join(d.get("note", "") for d in docs)
        return {"patient_id": patient_id, "referrals": notes, "records": docs}

class PharmacyAgent:
    """Pharmacy agent: checks active medications for a patient."""
    def fetch(self, patient_id: str) -> Dict[str, Any]:
        col = get_collection("medications")
        docs = list(col.find({"patient_id": patient_id}).sort("effective_date", -1))
        # Simplify: medications is a list of med names
        meds = [d.get("medication") for d in docs]
        return {"patient_id": patient_id, "medications": meds, "records": docs}
