from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.orchestrator import orchestrate_and_write

app = FastAPI()

class OrchestrateRequest(BaseModel):
    patient_id: str

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    try:
        res = orchestrate_and_write(req.patient_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
