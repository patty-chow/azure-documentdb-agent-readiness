from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from .db import safe_create_indexes
from .agent import review_correspondent

app = FastAPI(title="Correspondent Risk Screener")

# Ensure basic indexes exist on startup
safe_create_indexes()


class ReviewRequest(BaseModel):
    correspondent_id: Optional[str] = None
    profile_text: Optional[str] = None


@app.post("/review")
async def review(req: ReviewRequest):
    try:
        result = review_correspondent(correspondent_id=req.correspondent_id, profile_text=req.profile_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
