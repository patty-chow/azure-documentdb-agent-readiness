import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List

from beanie.odm.operators import Greater, Less
from beanie import PydanticObjectId

from .models import LabResult
from .db import init_db, create_compound_index, get_client

app = FastAPI()

# Demo reference ranges (min, max, critical_low, critical_high)
REFERENCE_RANGES = {
    "HGB": (12.0, 18.0, 8.0, 25.0),
    "WBC": (4.0, 11.0, 1.0, 50.0),
    "GLU": (70.0, 140.0, 30.0, 500.0),
}

class LabResultIn(BaseModel):
    patientId: str
    testCode: str
    value: float
    timestamp: Optional[datetime] = None

@app.on_event("startup")
async def startup_event():
    await init_db()
    # ensure index exists
    await create_compound_index()
    # start change stream monitor
    loop = asyncio.get_event_loop()
    loop.create_task(change_stream_monitor())

@app.post("/results")
async def insert_result(payload: LabResultIn):
    doc = LabResult(
        patientId=payload.patientId,
        testCode=payload.testCode,
        value=payload.value,
        timestamp=payload.timestamp or datetime.utcnow(),
    )
    await doc.insert()
    return {"id": str(doc.id)}

@app.get("/patients/{patient_id}/tests/{test_code}/moving-average")
async def moving_average(patient_id: str, test_code: str, window:int=5):
    # Use aggregation pipeline with $setWindowFields partitioned by patientId+testCode
    pipeline = [
        {"$match": {"patientId": patient_id, "testCode": test_code}},
        {"$setWindowFields": {
            "partitionBy": {"patientId": "$patientId", "testCode": "$testCode"},
            "sortBy": {"timestamp": 1},
            "output": {
                "movingAvg": {"$avg": "$value", "window": {"documents": [-(window-1), 0]}}
            }
        }},
        {"$project": {"_id": 0, "patientId":1, "testCode":1, "timestamp":1, "value":1, "movingAvg":1}}
    ]
    client = await get_client()
    cursor = client["sample_healthcare_07"]["lab_results"].aggregate(pipeline)
    results = [r async for r in cursor]
    return results

@app.get("/patients/{patient_id}/tests/{test_code}/out-of-range")
async def out_of_range(patient_id: str, test_code: str):
    # Find latest values for the patient/test and flag outs
    rng = REFERENCE_RANGES.get(test_code)
    if not rng:
        raise HTTPException(status_code=404, detail="Reference range not found for test code")
    minv, maxv, critical_low, critical_high = rng
    docs = await LabResult.find({"patientId": patient_id, "testCode": test_code}).sort(-LabResult.timestamp).to_list()
    flagged = []
    for d in docs:
        flag = None
        if d.value < minv or d.value > maxv:
            flag = "out_of_reference"
        if d.value < critical_low or d.value > critical_high:
            flag = "critical"
        if flag:
            flagged.append({"id": str(d.id), "timestamp": d.timestamp, "value": d.value, "flag": flag})
    return flagged

async def change_stream_monitor():
    # Open a change stream and log critical alerts when they appear
    client = await get_client()
    coll = client["sample_healthcare_07"]["lab_results"]
    try:
        async with coll.watch(full_document='updateLookup') as stream:
            async for change in stream:
                full = change.get('fullDocument') or {}
                if not full:
                    continue
                test_code = full.get('testCode')
                value = full.get('value')
                patient_id = full.get('patientId')
                rng = REFERENCE_RANGES.get(test_code)
                if rng:
                    _, _, critical_low, critical_high = rng
                    if value is not None and (value < critical_low or value > critical_high):
                        # Emit alert (console for sample)
                        print(f"ALERT: patient={patient_id} test={test_code} value={value} is CRITICAL (thresholds {critical_low},{critical_high})")
    except Exception as e:
        print("Change stream monitor stopped with error:", e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
