import os
import asyncio
import random
from datetime import datetime, timedelta
from src.db import init_db, create_compound_index, get_client
from src.models import LabResult

PATIENTS = [f"patient_{i:03d}" for i in range(1, 11)]
TESTS = ["HGB", "WBC", "GLU"]

RANGES = {
    "HGB": (12.0, 18.0, 8.0, 25.0),
    "WBC": (4.0, 11.0, 1.0, 50.0),
    "GLU": (70.0, 140.0, 30.0, 500.0),
}

async def seed(n_per_patient=20):
    await init_db()
    await create_compound_index()
    client = await get_client()
    coll = client["sample_healthcare_07"]["lab_results"]
    # Clear sample collection (for demo only)
    await coll.delete_many({})
    docs = []
    now = datetime.utcnow()
    for p in PATIENTS:
        for _ in range(n_per_patient):
            test = random.choice(TESTS)
            low, high, clow, chigh = RANGES[test]
            # generate mostly normal values with a small chance of critical
            if random.random() < 0.02:
                val = random.choice([clow - random.random()*5, chigh + random.random()*50])
            else:
                val = random.uniform(low, high)
            ts = now - timedelta(minutes=random.randint(0, 60*24*30))
            docs.append({"patientId": p, "testCode": test, "value": val, "timestamp": ts})
    if docs:
        await coll.insert_many(docs)
    print(f"Inserted {len(docs)} documents")

if __name__ == "__main__":
    asyncio.run(seed())
