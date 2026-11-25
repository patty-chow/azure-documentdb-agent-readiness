"""Seed script for adverse event sample.

If OPENAI_API_KEY is set, this script will attempt to POST each sample free-text to the running API (if desired).
If OPENAI_API_KEY is NOT set, this script inserts pre-parsed structured sample documents directly into the DocumentDB collection.
"""
import os
from datetime import date
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
DB = os.getenv("DOCUMENTDB_DATABASE", "sample_healthcare_18")

if DOCUMENTDB_URI is None:
    raise RuntimeError("Set DOCUMENTDB_URI in env before running seed.py")

client = MongoClient(DOCUMENTDB_URI)
db = client[DB]
coll = db["adverse_events"]
# ensure compound index
coll.create_index([("drug", ASCENDING), ("event", ASCENDING)], name="idx_drug_event")

SAMPLES = [
    {
        "drug": "Aspirin",
        "event": "nausea",
        "severity": "mild",
        "onset_date": date(2023,5,1),
        "raw_text": "Patient experienced mild nausea after taking Aspirin.",
    },
    {
        "drug": "Aspirin",
        "event": "bleeding",
        "severity": "moderate",
        "onset_date": date(2023,5,3),
        "raw_text": "Moderate bleeding observed following Aspirin dose.",
    },
    {
        "drug": "Ibuprofen",
        "event": "dizziness",
        "severity": "mild",
        "onset_date": date(2023,6,2),
        "raw_text": "Dizziness reported after taking Ibuprofen.",
    },
    {
        "drug": "Ibuprofen",
        "event": "nausea",
        "severity": "mild",
        "onset_date": date(2023,6,5),
        "raw_text": "Nausea and upset stomach after Ibuprofen.",
    },
    {
        "drug": "Amoxicillin",
        "event": "rash",
        "severity": "severe",
        "onset_date": date(2023,4,20),
        "raw_text": "Severe rash developed while on Amoxicillin.",
    },
    {
        "drug": "Amoxicillin",
        "event": "nausea",
        "severity": "mild",
        "onset_date": date(2023,4,21),
        "raw_text": "Mild nausea noted.",
    },
    {
        "drug": "Paracetamol",
        "event": "headache",
        "severity": "mild",
        "onset_date": date(2023,7,1),
        "raw_text": "Headache persisted despite Paracetamol.",
    },
    {
        "drug": "Paracetamol",
        "event": "liver enzyme increase",
        "severity": "moderate",
        "onset_date": date(2023,7,2),
        "raw_text": "Moderate liver enzyme elevation following Paracetamol.",
    },
    {
        "drug": "Aspirin",
        "event": "nausea",
        "severity": "mild",
        "onset_date": date(2023,5,10),
        "raw_text": "Another nausea case after Aspirin.",
    },
    {
        "drug": "Ibuprofen",
        "event": "dizziness",
        "severity": "mild",
        "onset_date": date(2023,6,10),
        "raw_text": "Transient dizziness after Ibuprofen.",
    },
]

# Convert dates to ISO strings for pymongo
for s in SAMPLES:
    if isinstance(s.get("onset_date"), date):
        s["onset_date"] = s["onset_date"].isoformat()

# Insert with ordered=False to continue on duplicates
res = coll.insert_many(SAMPLES, ordered=False)
print(f"Inserted {len(res.inserted_ids)} sample documents into {DB}.adverse_events")
