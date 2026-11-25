from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .db import get_db

class Signal(BaseModel):
    strategy_id: str
    timestamp: datetime
    signal_type: str
    meta: Optional[dict] = None

class Execution(BaseModel):
    strategy_id: str
    timestamp: datetime
    side: str
    price: float
    quantity: float
    meta: Optional[dict] = None

class Outcome(BaseModel):
    strategy_id: str
    timestamp: datetime
    pnl: float = Field(..., description="Profit and loss for the trade (positive win, negative loss)")
    meta: Optional[dict] = None


def insert_event(doc: BaseModel, event_type: str):
    db = get_db()
    coll = db["journal"]
    payload = doc.dict()
    payload.update({"type": event_type})
    # immutable append-only insert
    return coll.insert_one(payload)

def insert_signal(signal: Signal):
    return insert_event(signal, "signal")

def insert_execution(execution: Execution):
    return insert_event(execution, "execution")

def insert_outcome(outcome: Outcome):
    return insert_event(outcome, "outcome")
