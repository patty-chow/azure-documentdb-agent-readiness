import asyncio
from fastapi import FastAPI, HTTPException
from .db import init_db, get_client, get_db_name
from .models import OnboardingApplication
from .orchestrator import orchestrate

app = FastAPI()


@app.on_event("startup")
async def startup():
    await init_db()


@app.post("/orchestrate")
async def api_orchestrate(applicant_id: str):
    try:
        result = await orchestrate(applicant_id)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/applications/{applicant_id}/status")
async def get_status(applicant_id: str):
    client = get_client()
    db_name = get_db_name()
    coll = client[db_name][OnboardingApplication.Collection.name]
    doc = await coll.find_one({"applicant_id": applicant_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {"applicant_id": applicant_id, "state": doc.get("state"), "history": doc.get("history", [])}
