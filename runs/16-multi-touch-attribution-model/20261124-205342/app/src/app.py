import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.db import get_db
from src.attribution import run_attribution_for_all
from src.langchain_tool import answer_question_for_customer

app = FastAPI(title="DocumentDB Attribution Sample")

class RunResponse(BaseModel):
    processed: int

class QueryRequest(BaseModel):
    customer_id: str
    question: str

@app.post("/run-attribution")
def run_attribution():
    db = get_db()
    summary = run_attribution_for_all(db)
    return summary

@app.post("/query")
def query(q: QueryRequest):
    db = get_db()
    try:
        answer = answer_question_for_customer(db, q.customer_id, q.question)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"answer": answer}
