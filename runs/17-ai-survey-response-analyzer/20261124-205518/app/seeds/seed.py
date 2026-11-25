"""Seed script: idempotently inserts sample survey responses into the target DB.
This script uses pymongo (sync) for simplicity.
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_customer_360_17")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI must be set in environment (.env)")

client = MongoClient(DOCUMENTDB_URI)
db = client[DATABASE_NAME]
col = db["survey_responses"]

examples = [
    {
        "survey_id": "s1",
        "question_id": "q1",
        "respondent_id": "r1",
        "response_text": "I love the product UI, it's intuitive and clean. Customer support was slow though.",
        "created_at": datetime.utcnow(),
    },
    {
        "survey_id": "s1",
        "question_id": "q1",
        "respondent_id": "r2",
        "response_text": "The new update broke some features. I'd like a rollback or hotfix. Pricing is reasonable.",
        "created_at": datetime.utcnow(),
    },
    {
        "survey_id": "s1",
        "question_id": "q2",
        "respondent_id": "r3",
        "response_text": "I find onboarding confusing; documentation could be better. But the feature set is great.",
        "created_at": datetime.utcnow(),
    },
    {
        "survey_id": "s2",
        "question_id": "q1",
        "respondent_id": "r4",
        "response_text": "Excellent performance and stability. No complaints.",
        "created_at": datetime.utcnow(),
    },
]

# Idempotent insert: upsert by hash of text + respondent
for doc in examples:
    key = {"survey_id": doc["survey_id"], "question_id": doc["question_id"], "respondent_id": doc["respondent_id"]}
    col.update_one(key, {"$setOnInsert": doc}, upsert=True)

print(f"Seeded {len(examples)} sample documents into {DATABASE_NAME}.survey_responses")
