import asyncio
from dotenv import load_dotenv
from src.db import init_db, get_client, close_client
from src.models import LoanApplication
from src.orchestrator import run_for_demo

load_dotenv()

async def main():
    # Ensure DB models are registered
    await init_db([LoanApplication])
    # Find the sample application by applicant.ssn_last4
    client = await get_client()
    db = client.get_database("sample_fintech_14")
    coll = db.get_collection("loan_applications")
    doc = await coll.find_one({"applicant.ssn_last4": "1234"})
    if not doc:
        print("No sample application found. Run scripts/seed.py first.")
        return
    app_id = doc["_id"]
    print("Starting orchestrator for application id:", app_id)
    await run_for_demo(app_id)
    # Print final document
    final = await coll.find_one({"_id": app_id})
    from pprint import pprint
    pprint(final)
    await close_client()

if __name__ == '__main__':
    asyncio.run(main())
