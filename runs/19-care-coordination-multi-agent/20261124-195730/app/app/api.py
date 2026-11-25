from fastapi import FastAPI
from pydantic import BaseModel
from .orchestrator import orchestrate_patient

app = FastAPI()

class OrchestrateRequest(BaseModel):
    patient_id: str

@app.post('/orchestrate')
async def orchestrate(req: OrchestrateRequest):
    doc = orchestrate_patient(req.patient_id)
    # return a lightweight summary
    return {"patient_id": doc["patient_id"], "care_plan_id": str(doc["_id"])}
