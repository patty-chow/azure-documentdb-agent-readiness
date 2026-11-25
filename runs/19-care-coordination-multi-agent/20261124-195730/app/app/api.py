from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .orchestrator import Orchestrator

app = FastAPI(title="Care Coordination Orchestrator")
orch = Orchestrator()

class OrchestrateRequest(BaseModel):
    patient_id: str

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    try:
        res = orch.orchestrate(req.patient_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
