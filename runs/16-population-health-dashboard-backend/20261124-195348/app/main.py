from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from db import get_db
from aggregations import compute_facets, upsert_summary, get_cached_summary
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import hashlib
import json

app = FastAPI(title="Population Health Dashboard Backend")
scheduler = BackgroundScheduler()
DEFAULT_SUMMARY_NAME = "default_cohort"


def _params_from_query(q: dict) -> dict:
    # extract the supported params
    params = {}
    if q.get("min_age") is not None:
        params["min_age"] = q.get("min_age")
    if q.get("max_age") is not None:
        params["max_age"] = q.get("max_age")
    if q.get("gender"):
        params["gender"] = q.get("gender")
    if q.get("region"):
        params["region"] = q.get("region")
    if q.get("diagnosis"):
        params["diagnosis"] = q.get("diagnosis")
    return params


@app.on_event("startup")
def startup_event():
    # validate DB connectivity and ensure indexes on cache
    db = get_db()
    cache = db.aggregations_cache
    # TTL index on expiresAt
    cache.create_index([("expiresAt", 1)], expireAfterSeconds=0)

    # schedule periodic refresh every hour
    scheduler.add_job(func=refresh_default_summary, trigger="interval", hours=1, id="refresh_default")
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)


def refresh_default_summary():
    db = get_db()
    patients = db.patients
    cache = db.aggregations_cache
    params = {}  # default: whole cohort
    try:
        summary = compute_facets(patients, params)
        upsert_summary(cache, DEFAULT_SUMMARY_NAME, params, summary)
        print(f"Refreshed default summary at {datetime.utcnow().isoformat()}")
    except Exception as e:
        print(f"Failed to refresh summary: {e}")


@app.get("/facets")
def facets(use_cache: Optional[bool] = True, min_age: Optional[int] = None, max_age: Optional[int] = None, gender: Optional[str] = None, region: Optional[str] = None, diagnosis: Optional[str] = None):
    db = get_db()
    patients = db.patients
    cache = db.aggregations_cache
    params = _params_from_query({"min_age": min_age, "max_age": max_age, "gender": gender, "region": region, "diagnosis": diagnosis})
    if use_cache:
        cached = get_cached_summary(cache, "facets", params)
        if cached:
            return JSONResponse({"cached": True, "summary": cached["summary"], "createdAt": cached.get("createdAt")})
    # compute live
    try:
        summary = compute_facets(patients, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # optionally store cache
    if use_cache:
        upsert_summary(cache, "facets", params, summary)
    return JSONResponse({"cached": False, "summary": summary})


@app.post("/summaries/refresh")
def trigger_refresh(background_tasks: BackgroundTasks):
    # run refresh in background to avoid blocking
    background_tasks.add_task(refresh_default_summary)
    return {"status": "refresh scheduled"}


@app.get("/summaries/{name}")
def get_summary(name: str, min_age: Optional[int] = None, max_age: Optional[int] = None, gender: Optional[str] = None, region: Optional[str] = None, diagnosis: Optional[str] = None):
    db = get_db()
    cache = db.aggregations_cache
    params = _params_from_query({"min_age": min_age, "max_age": max_age, "gender": gender, "region": region, "diagnosis": diagnosis})
    doc = get_cached_summary(cache, name, params)
    if not doc:
        raise HTTPException(status_code=404, detail="Summary not found")
    # remove internal fields
    return {"name": doc.get("name"), "params": doc.get("params"), "summary": doc.get("summary"), "createdAt": doc.get("createdAt")}
