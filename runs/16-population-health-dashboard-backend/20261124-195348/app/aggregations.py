import hashlib
import json
from datetime import datetime, timedelta
from pymongo.collection import Collection
from typing import Any, Dict, Optional

TTL_SECONDS = 24 * 3600  # cached summaries live 24 hours by default


def _params_hash(params: Dict[str, Any]) -> str:
    # Deterministic JSON hashing for cache key
    j = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(j.encode("utf-8")).hexdigest()


def build_match_from_params(params: Dict[str, Any]) -> Dict[str, Any]:
    match: Dict[str, Any] = {}
    if "min_age" in params or "max_age" in params:
        age_filter: Dict[str, Any] = {}
        if "min_age" in params:
            age_filter["$gte"] = int(params["min_age"])
        if "max_age" in params:
            age_filter["$lte"] = int(params["max_age"])
        match["age"] = age_filter
    if "gender" in params:
        match["gender"] = {"$in": [g.strip() for g in params["gender"].split(",") if g.strip()]}
    if "region" in params:
        match["region"] = {"$in": [r.strip() for r in params["region"].split(",") if r.strip()]}
    if "diagnosis" in params:
        # match any patient with that diagnosis code in the diagnoses array
        match["diagnoses"] = {"$in": [params["diagnosis"]]}
    return match


def build_facet_pipeline(match: Optional[Dict[str, Any]] = None):
    if match is None:
        match = {}
    pipeline = []
    if match:
        pipeline.append({"$match": match})

    facet_stage = {
        "$facet": {
            "diagnoses": [
                {"$unwind": "$diagnoses"},
                {"$group": {"_id": "$diagnoses", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ],
            "age_bands": [
                {
                    "$bucket": {
                        "groupBy": "$age",
                        "boundaries": [0, 18, 35, 50, 65, 120],
                        "default": "unknown",
                        "output": {"count": {"$sum": 1}},
                    }
                }
            ],
            "gender": [
                {"$group": {"_id": "$gender", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ],
            "region": [
                {"$group": {"_id": "$region", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ],
        }
    }
    pipeline.append(facet_stage)
    return pipeline


def compute_facets(patients_coll: Collection, params: Dict[str, Any]) -> Dict[str, Any]:
    match = build_match_from_params(params)
    pipeline = build_facet_pipeline(match)
    # Run aggregation
    cursor = patients_coll.aggregate(pipeline, allowDiskUse=False)
    results = list(cursor)
    # aggregation returns single document with the facets
    return results[0] if results else {"diagnoses": [], "age_bands": [], "gender": [], "region": []}


def upsert_summary(cache_coll: Collection, name: str, params: Dict[str, Any], summary: Dict[str, Any]):
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=TTL_SECONDS)
    key = _params_hash({"name": name, "params": params})
    doc = {
        "_id": key,
        "name": name,
        "params": params,
        "summary": summary,
        "createdAt": now,
        "expiresAt": expires_at,
    }
    # upsert
    cache_coll.update_one({"_id": key}, {"$set": doc}, upsert=True)
    return doc


def get_cached_summary(cache_coll: Collection, name: str, params: Dict[str, Any]):
    key = _params_hash({"name": name, "params": params})
    return cache_coll.find_one({"_id": key})
