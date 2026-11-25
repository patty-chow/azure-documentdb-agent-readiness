from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
from src import agent, db

app = FastAPI()


class QueryRequest(BaseModel):
    client_id: str
    question: str


@app.post("/query")
def query(req: QueryRequest) -> Any:
    try:
        result = agent.answer_question(req.client_id, req.question)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/seed")
def seed():
    # Convenience endpoint to run the seed script via HTTP (not recommended for prod)
    db.ensure_collections_and_indexes()
    return {"status": "indexes ensured"}
