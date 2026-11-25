from fastapi import FastAPI
from pydantic import BaseModel
from src.analyze import analyze_text

app = FastAPI()

class AnalyzeRequest(BaseModel):
    excerpt: str


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    return analyze_text(req.excerpt)
