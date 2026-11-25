from fastapi import FastAPI
from pydantic import BaseModel
from .agents import Orchestrator

app = FastAPI()
orch = Orchestrator()

class ReorderRequest(BaseModel):
    item_id: str | None = None

@app.post("/reorder")
async def reorder(req: ReorderRequest):
    if req.item_id:
        po = orch.create_purchase_order(req.item_id)
        return {"po": po}
    else:
        res = orch.run_for_all()
        return {"created": len(res)}
