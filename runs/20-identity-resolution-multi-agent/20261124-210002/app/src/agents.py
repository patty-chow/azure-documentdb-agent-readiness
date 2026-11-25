import os
import asyncio
from typing import List, Dict, Any
from .models import Profile, GoldenRecord, AuditEntry
from .db import init_db, get_client, BEANIE_OK
import numpy as np

try:
    import openai
except Exception:
    openai = None

EMBED_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.environ.get("OPENAI_API_MODEL", "gpt-3.5-turbo")

async def compute_embedding(text: str):
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key and openai:
        openai.api_key = api_key
        resp = openai.Embedding.create(model=EMBED_MODEL, input=text)
        return resp['data'][0]['embedding']
    else:
        # synthetic
        vec = np.random.normal(size=(1536,))
        return (vec/np.linalg.norm(vec)).tolist()

async def match_agent(profile_id: str, k=5, lSearch=100):
    """Given a profile id, find top-k candidate duplicates using vector search."""
    await init_db()
    client = await get_client()
    db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_20")
    coll = client[db_name]["profiles"]

    # fetch the profile
    target = await coll.find_one({"_id": profile_id})
    if not target or not target.get('embedding'):
        return []
    qv = target['embedding']
    pipeline = [
        {"$search": {"cosmosSearch": {"path": "embedding", "vector": qv, "k": k, "lSearch": lSearch}}},
        {"$project": {"_id": 1, "name": 1, "emails": 1, "score": {"$meta": "searchScore"}}},
        {"$limit": k}
    ]
    try:
        curs = coll.aggregate(pipeline)
        res = []
        async for r in curs:
            res.append(r)
        return res
    except Exception:
        # Fallback: brute-force cosine similarity
        docs = coll.find({})
        candidates = []
        async for d in docs:
            if d.get('_id') == profile_id: continue
            a = np.array(qv)
            b = np.array(d.get('embedding') or np.zeros_like(a))
            sim = float(np.dot(a, b) / (np.linalg.norm(a) * (np.linalg.norm(b) + 1e-9)))
            candidates.append({'_id': d['_id'], 'name': d.get('name'), 'emails': d.get('emails'), 'score': sim})
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:k]

async def merge_agent(candidates: List[Dict[str, Any]]):
    """Given candidate docs, ask an LLM to choose merge strategy and return golden record + confidence."""
    # Simple rule-based merge if no LLM
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or openai is None:
        # deterministic merge: union of emails, longest name
        merged = {}
        emails = set()
        names = []
        for c in candidates:
            if c.get('emails'): emails.update(c['emails'])
            if c.get('name'): names.append(c['name'])
        merged['name'] = max(names, key=lambda x: len(x)) if names else None
        merged['emails'] = list(emails)
        return merged, 0.6, "rule-based"

    # else call OpenAI chat to ask for merge plan
    msgs = [
        {"role":"system","content":"You are a data engineer assistant that consolidates several person profiles into a single golden record. Prefer verified emails and longer names."},
        {"role":"user","content": f"Given these candidate profiles: {candidates}, produce a merged record (json) and a confidence score between 0 and 1."}
    ]
    openai.api_key = api_key
    resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=msgs, max_tokens=512)
    text = resp['choices'][0]['message']['content']
    # attempt to parse JSON from model — naive
    import json, re
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}, 0.0, text
    try:
        merged = json.loads(m.group(0))
        # if model didn't return confidence, set heuristic
        confidence = merged.pop('confidence', None) or 0.8
        return merged, float(confidence), "llm"
    except Exception:
        return {}, 0.0, text

async def audit_agent(merged_record: Dict[str, Any], merged_ids: List[str], confidence: float, source_docs: List[Dict[str, Any]], note: str = None):
    # attempt beanie-based insert; fallback to motor insert
    try:
        await init_db()
    except Exception:
        pass
    if BEANIE_OK:
        entry = AuditEntry(merged_ids=[str(i) for i in merged_ids], confidence=confidence, source_docs=source_docs, note=note)
        await entry.insert()
        return entry
    else:
        client = await get_client()
        db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_20")
        coll = client[db_name]["merge_audits"]
        doc = {"merged_ids":[str(i) for i in merged_ids], "confidence":confidence, "source_docs":source_docs, "note":note}
        res = await coll.insert_one(doc)
        doc['_id'] = res.inserted_id
        return doc

async def write_golden(merged: Dict[str, Any], provenance: List[str]):
    try:
        await init_db()
    except Exception:
        pass
    if BEANIE_OK:
        gr = GoldenRecord(merged=merged, provenance=provenance)
        await gr.insert()
        return gr
    else:
        client = await get_client()
        db_name = os.environ.get("DATABASE_NAME", "sample_customer_360_20")
        coll = client[db_name]["golden_profiles"]
        doc = {"merged":merged, "provenance":provenance}
        res = await coll.insert_one(doc)
        doc['_id'] = res.inserted_id
        return doc
