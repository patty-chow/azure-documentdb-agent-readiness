import os
import json
from datetime import datetime
from typing import Dict, Any

import openai
from .db import get_collections

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def _fallback_summarize(transcript: str) -> Dict[str, Any]:
    # Very small heuristic fallback for environments without OpenAI credentials.
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    first = lines[0] if lines else transcript[:200]
    rest = " ".join(lines[1:]) if len(lines) > 1 else ""
    return {
        "chief_complaint": first[:100],
        "assessment": (rest[:400] or "Likely follow-up needed."),
        "plan": "Recommend follow-up and basic symptomatic treatment.",
        "follow_up": "Follow up in 1 week or earlier if worsening.",
    }


def _call_openai_for_summary(transcript: str) -> Dict[str, Any]:
    system_prompt = (
        "You are a clinical summarisation assistant. Given a telehealth session transcript, "
        "extract and return a JSON object with the following keys: chief_complaint, assessment, plan, follow_up. "
        "Be concise and factual. Return only a valid JSON object with those keys."
    )

    user_prompt = (
        "Transcript:\n" + transcript + "\n\n"
        "Provide the structured clinical summary as JSON with keys: chief_complaint, assessment, plan, follow_up."
    )

    resp = openai.ChatCompletion.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=800,
    )
    text = resp["choices"][0]["message"]["content"].strip()
    # Attempt to parse JSON out of the response. If fails, raise.
    try:
        data = json.loads(text)
        return data
    except Exception:
        # Attempt to find a JSON substring
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        raise


def summarize_transcript(transcript: str, patient_id: str) -> Dict[str, Any]:
    """Summarize a telehealth transcript and store the structured summary in DocumentDB.

    Returns the stored document.
    """
    collections = get_collections()
    clinical_col = collections["clinical_summaries"]

    if OPENAI_API_KEY:
        try:
            summary = _call_openai_for_summary(transcript)
        except Exception as e:
            # Fall back to heuristic if OpenAI fails
            print("OpenAI call failed; using fallback summariser:", e)
            summary = _fallback_summarize(transcript)
    else:
        summary = _fallback_summarize(transcript)

    doc = {
        "patientId": patient_id,
        "chief_complaint": summary.get("chief_complaint"),
        "assessment": summary.get("assessment"),
        "plan": summary.get("plan"),
        "follow_up": summary.get("follow_up"),
        "createdAt": datetime.utcnow(),
        "schemaVersion": 1,
    }

    res = clinical_col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc
