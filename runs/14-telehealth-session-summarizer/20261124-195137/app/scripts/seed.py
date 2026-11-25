"""Idempotent seed script: upserts a sample patient and some transcripts."""
import os
import sys
from datetime import datetime
from pymongo import ReturnDocument

# ensure src is importable when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db import get_collections, create_indexes


def seed():
    create_indexes()
    cols = get_collections()
    patients = cols["patients"]
    transcripts = cols["transcripts"]

    # Upsert a deterministic patient record
    patient = {
        "patientId": "patient_1",
        "name": "John Doe",
        "dob": "1980-01-01",
        "createdAt": datetime.utcnow(),
    }
    patients.update_one({"patientId": patient["patientId"]}, {"$set": patient}, upsert=True)

    sample_transcripts = [
        {
            "sessionId": "session_1",
            "patientId": "patient_1",
            "timestamp": datetime.utcnow(),
            "transcript": "Patient reports headache for 2 days. Nausea but no vomiting. No chest pain.\nProvider: Take acetaminophen and rest, return if worse.",
        },
        {
            "sessionId": "session_2",
            "patientId": "patient_1",
            "timestamp": datetime.utcnow(),
            "transcript": "Patient describes cough and sore throat for 3 days. Low-grade fever.\nProvider: Recommend symptomatic care, consider RTC if breathing worsens.",
        },
    ]

    for t in sample_transcripts:
        transcripts.update_one({"sessionId": t["sessionId"]}, {"$set": t}, upsert=True)

    print("Seed completed.")


if __name__ == "__main__":
    seed()
