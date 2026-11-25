from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()
from .embeddings import embed_vector_from_features
from .retriever import retrieve_similar, ensure_vector_index
from .agent import generate_narrative

app = FastAPI(title="Chronic Disease Risk Predictor Sample")

TOP_K = int(os.environ.get("TOP_K", "5"))


class PatientFeatures(BaseModel):
    features: dict


@app.on_event("startup")
def startup_event():
    # Try to ensure vector index exists; ignore errors but log
    try:
        ensure_vector_index()
    except Exception:
        pass


@app.post("/predict")
def predict(payload: PatientFeatures):
    try:
        vec = embed_vector_from_features(payload.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        results = retrieve_similar(vec, k=TOP_K)
    except Exception:
        # Fallback: no server-side vector search available
        results = []

    narrative = generate_narrative(f"Patient features: {payload.features}", results)

    return {"narrative": narrative, "retrieved": results}
