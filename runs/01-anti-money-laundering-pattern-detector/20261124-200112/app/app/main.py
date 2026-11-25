from fastapi import FastAPI
from pydantic import BaseModel
from aml_agent.analysis import analyze
from aml_agent.llm import get_llm_client

app = FastAPI()

class AnalyzeRequest(BaseModel):
    use_llm: bool = False

@app.post("/analyze")
async def run_analysis(req: AnalyzeRequest):
    llm = None
    if req.use_llm:
        llm = get_llm_client()
    results = analyze(use_llm=req.use_llm, llm_client=llm)
    return {"results": results}
