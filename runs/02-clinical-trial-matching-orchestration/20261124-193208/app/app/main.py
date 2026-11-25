import os
import math
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.db import get_db

# LangChain/OpenAI imports (used if OPENAI_API_KEY is present)
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    ChatOpenAI = None
    HumanMessage = None
    OPENAI_AVAILABLE = False

EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

app = FastAPI(title="Clinical Trial Matching Sample")

class PatientProfile(BaseModel):
    age: int
    conditions: List[str] = []
    labs: Dict[str, float] = {}
    notes: str = ""

class MatchResult(BaseModel):
    trial_id: str
    title: str
    score: float
    eligible: bool
    eligibility_rationale: str
    consent_summary: str


# utility embedding / similarity helpers

def l2_norm(v):
    a = np.array(v, dtype=float)
    norm = np.linalg.norm(a)
    if norm == 0:
        return a
    return a / norm


def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# Simple deterministic eligibility engine (rules-based)

def deterministic_eligibility_check(trial: Dict[str, Any], patient: Dict[str, Any]):
    crit = trial.get("criteria", {})
    reasons = []
    eligible = True
    age = patient.get("age")
    if "min_age" in crit and age < crit.get("min_age"):
        eligible = False
        reasons.append(f"Patient age {age} is below minimum {crit.get('min_age')}")
    if "max_age" in crit and age > crit.get("max_age"):
        eligible = False
        reasons.append(f"Patient age {age} is above maximum {crit.get('max_age')}")
    required_conditions = set([c.lower() for c in crit.get("conditions", [])])
    patient_conditions = set([c.lower() for c in patient.get("conditions", [])])
    missing = required_conditions - patient_conditions
    if missing:
        eligible = False
        reasons.append(f"Missing required conditions: {', '.join(missing)}")
    # labs checks (simple >= threshold semantics)
    for lab, thresh in crit.get("labs", {}).items():
        pv = patient.get("labs", {}).get(lab)
        if pv is None:
            eligible = False
            reasons.append(f"Missing lab {lab}")
        else:
            if pv < thresh:
                eligible = False
                reasons.append(f"Lab {lab} value {pv} below required {thresh}")
    return eligible, "; ".join(reasons) if reasons else "Meets criteria"


# LLM powered rationale and consent summary (optional)

def llm_rationale_and_consent(trial: Dict[str, Any], patient: Dict[str, Any], eligible: bool):
    key = os.environ.get("OPENAI_API_KEY")
    if not key or not OPENAI_AVAILABLE:
        # fallback to templated text
        rationale = "Eligibility determined by deterministic rules (no LLM available)."
        consent = f"Trial '{trial.get('title')}'. Brief summary: {trial.get('summary', '')}"
        return rationale, consent

    # use LangChain Chat model
    chat = ChatOpenAI(model_name=LLM_MODEL, temperature=0)
    # eligibility rationale prompt
    prompt_r = (
        f"You are an assistant that summarizes clinical eligibility decisions.\n"
        f"Trial: {trial.get('title')}\nCriteria: {trial.get('criteria')}\nPatient profile: {patient}\n"
        f"Decision: {'Eligible' if eligible else 'Not eligible'}\n"
        f"Provide a concise rationale focusing on inclusion/exclusion items."
    )
    rationale = chat([HumanMessage(content=prompt_r)]).content

    # consent summary prompt
    prompt_c = (
        f"You are an assistant that explains clinical trials to a patient in plain language.\n"
        f"Trial title: {trial.get('title')}\nSummary: {trial.get('summary','No summary provided.')}\n"
        f"If the patient is not eligible, adapt the tone and explain why briefly.\n"
        f"Keep it under 120 words and avoid medical jargon."
    )
    consent = chat([HumanMessage(content=prompt_c)]).content
    return rationale, consent


def rank_and_match(patient: Dict[str, Any], top_k: int = 5) -> List[MatchResult]:
    db = get_db()
    coll = db.get_collection(os.environ.get("COLLECTION_NAME", "trials"))

    # simple prefilter: find trials that mention any patient condition
    patient_conditions = [c.lower() for c in patient.get("conditions", [])]
    filter_q = {}
    if patient_conditions:
        # find any trial whose criteria.conditions intersects the patient conditions
        filter_q = {"criteria.conditions": {"$in": patient_conditions}}

    docs = list(coll.find(filter_q).limit(200))

    # compute or fallback embedding for patient
    emb = None
    if os.environ.get("OPENAI_API_KEY") and OPENAI_AVAILABLE:
        # prefer using OpenAI embedding via langchain/openai lib when available
        try:
            import openai
            resp = openai.Embedding.create(input=patient.get("notes",""), model=os.environ.get("EMBEDDING_MODEL","text-embedding-3-small"))
            emb = resp["data"][0]["embedding"]
        except Exception:
            emb = None
    if emb is None:
        # fallback: average of condition tokens hashed (not meaningful but deterministic)
        # if trials have embeddings stored, we can still compute similarity
        emb = np.random.RandomState(sum([len(s) for s in patient.get('conditions',[])]) + patient.get('age',0)).randn(EMBEDDING_DIM).tolist()

    # rank candidates by cosine similarity against stored embedding (if present)
    scored = []
    for d in docs:
        d_emb = d.get("embedding")
        if d_emb:
            score = cosine_similarity(emb, d_emb)
        else:
            score = 0.0
        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, trial in scored[:top_k]:
        eligible, rationale_det = deterministic_eligibility_check(trial, patient)
        # try to call LLM for nicer rationale/consent
        rationale, consent = llm_rationale_and_consent(trial, patient, eligible)
        # if LLM not used, use deterministic rationale
        if not rationale or ("deterministic rules" in rationale):
            rationale = rationale_det
        match = MatchResult(
            trial_id=str(trial.get("trial_id", trial.get("_id"))),
            title=trial.get("title", "Untitled"),
            score=score,
            eligible=eligible,
            eligibility_rationale=rationale,
            consent_summary=consent,
        )
        results.append(match)

        # store match result in DB
        db.matches.insert_one({
            "trial_id": match.trial_id,
            "patient_profile": patient,
            "score": match.score,
            "eligible": match.eligible,
            "eligibility_rationale": match.eligibility_rationale,
            "consent_summary": match.consent_summary,
        })

    return results


@app.post("/match", response_model=List[MatchResult])
def match_endpoint(profile: PatientProfile):
    try:
        results = rank_and_match(profile.dict())
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Expose programmatic helper for demo/tests

def match_patient(profile: Dict[str, Any]):
    return [r.dict() for r in rank_and_match(profile)]
