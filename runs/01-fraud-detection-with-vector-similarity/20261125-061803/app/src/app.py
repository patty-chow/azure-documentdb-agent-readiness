from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from dotenv import load_dotenv
import os

load_dotenv()

from .agent import FraudAgent

app = FastAPI(title="DocumentDB Fraud Detection Sample")
agent = FraudAgent()

class Transaction(BaseModel):
    tx_id: str
    amount: float
    description: str = ""

@app.post("/score")
def score(tx: Transaction) -> Dict[str, Any]:
    try:
        result = agent.score_transaction(tx.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
