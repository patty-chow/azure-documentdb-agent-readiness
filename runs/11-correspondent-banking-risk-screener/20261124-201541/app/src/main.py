from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import search_correspondent

app = FastAPI(title="Correspondent Risk Screener")

class ReviewRequest(BaseModel):
    correspondent_id: str


@app.post("/review")
async def review(req: ReviewRequest):
    try:
        result = search_correspondent(req.correspondent_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
