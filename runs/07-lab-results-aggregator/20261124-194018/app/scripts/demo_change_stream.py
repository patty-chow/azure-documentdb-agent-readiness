import os
import asyncio
from datetime import datetime
from src.db import init_db, get_client

async def run_demo():
    await init_db()
    client = await get_client()
    coll = client["sample_healthcare_07"]["lab_results"]

    async def watch_once():
        async with coll.watch(full_document='updateLookup') as stream:
            # consume a single event then return
            change = await stream.next()
            full = change.get('fullDocument')
            print('Change stream saw:', full)
            return full

    async def insert_critical():
        # insert a critical GLU value to trigger alert
        doc = {"patientId": "patient_001", "testCode": "GLU", "value": 600.0, "timestamp": datetime.utcnow()}
        res = await coll.insert_one(doc)
        print('Inserted critical doc id', res.inserted_id)

    watcher = asyncio.create_task(watch_once())
    await asyncio.sleep(0.5)
    await insert_critical()
    try:
        await asyncio.wait_for(watcher, timeout=10.0)
    except asyncio.TimeoutError:
        print('Watcher timed out waiting for change')

if __name__ == "__main__":
    asyncio.run(run_demo())
