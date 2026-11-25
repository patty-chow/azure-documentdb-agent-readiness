import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from src.db import init_db, get_client, close_client
from src.models import LoanApplication, Applicant, Transition

async def seed():
    await init_db([LoanApplication])
    # Upsert a sample application with a fixed unique key (use applicant.ssn_last4 to dedupe)
    sample = {
        "applicant": {
            "name": "Alice Example",
            "ssn_last4": "1234",
            "credit_score": 720,
            "requested_amount": 25000
        },
        "current_state": "submitted",
        "transitions": []
    }
    # Use replace_one with upsert using ssn_last4 as unique selector
    client = await get_client()
    db = client.get_database("sample_fintech_14")
    coll = db.get_collection("loan_applications")
    res = await coll.update_one({"applicant.ssn_last4": sample["applicant"]["ssn_last4"]}, {"$setOnInsert": sample}, upsert=True)
    print("Seed complete. upserted_id:", res.upserted_id)
    await close_client()

if __name__ == '__main__':
    asyncio.run(seed())
