from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from src.agent import run_agent_assign_segment

load_dotenv()

app = FastAPI()

class SegmentRequest(BaseModel):
    customer_id: str
    use_llm: bool = False

@app.post("/segment")
async def segment(req: SegmentRequest):
    try:
        res = run_agent_assign_segment(req.customer_id, use_llm=req.use_llm)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
