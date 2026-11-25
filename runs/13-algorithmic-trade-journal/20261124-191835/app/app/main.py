from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional
from .db import ensure_indexes
from .journal import Signal, Execution, Outcome, insert_signal, insert_execution, insert_outcome
from .aggregations import stats_for_strategy
from .formatter import format_strategy_review

app = FastAPI(title="Algo Trade Journal")

@app.on_event("startup")
def startup():
    # ensure indexes
    ensure_indexes()

@app.post("/journal/signal")
def post_signal(payload: Signal):
    insert_signal(payload)
    return {"status": "ok"}

@app.post("/journal/execution")
def post_execution(payload: Execution):
    insert_execution(payload)
    return {"status": "ok"}

@app.post("/journal/outcome")
def post_outcome(payload: Outcome):
    insert_outcome(payload)
    return {"status": "ok"}

@app.get("/stats/{strategy_id}")
def get_stats(strategy_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None):
    stats = stats_for_strategy(strategy_id, start, end)
    summary = format_strategy_review(stats)
    return {"stats": stats, "summary": summary}
