import os
import json
from typing import Dict, Any

from .db import get_db

# LLM calls are optional. If OPENAI_API_KEY is not set or mock=True is passed,
# the functions will return deterministic outputs suitable for tests.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def fetch_applicant(applicant_id: str) -> Dict[str, Any]:
    db = get_db()
    doc = db.applicants.find_one({"_id": applicant_id})
    if not doc:
        raise KeyError(f"Applicant {applicant_id} not found")
    return doc


def _rule_based_base_score(applicant: Dict[str, Any]) -> int:
    # A simple deterministic baseline scoring rule for demonstration.
    income = applicant.get("income", 0)
    debts = applicant.get("debts", 0)
    num_defaults = sum(1 for l in applicant.get("pastLoans", []) if l.get("status") == "default")

    score = 600
    # higher income raises score
    if income > 100_000:
        score += 100
    elif income > 50_000:
        score += 50

    # debts lower the score
    if debts > 50_000:
        score -= 100
    elif debts > 20_000:
        score -= 50

    # defaults penalize
    score -= num_defaults * 100
    # clip
    score = max(300, min(850, score))
    return score


def score_applicant(applicant: Dict[str, Any], use_llm: bool = False, mock: bool = False) -> Dict[str, Any]:
    base = _rule_based_base_score(applicant)
    details = {"base_score": base}

    if mock or not use_llm or not OPENAI_API_KEY:
        # Mock or no-LLM flow: return base with a small deterministic adjustment
        final = base + 0
        details["llm_applied"] = False
        return {"final_score": final, "details": details}

    # Real LLM flow: call OpenAI via a simple prompt to refine score
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"Applicant data: {json.dumps(applicant)}\n\nBased on the data, what numeric credit score (300-850) would you assign? Respond only with a JSON object: {json.dumps({'score':'<int>','notes':'<text>'})}"
        resp = client.chat.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
        text = resp.choices[0].message.content
        # Try parse JSON from LLM
        parsed = json.loads(text)
        final = int(parsed.get("score", base))
        details["llm_applied"] = True
        details["llm_notes"] = parsed.get("notes")
        details["llm_raw"] = text
        return {"final_score": max(300, min(850, final)), "details": details}
    except Exception as e:
        # On any error fallback to base score
        details["llm_error"] = str(e)
        details["llm_applied"] = False
        return {"final_score": base, "details": details}


def explain_score(applicant: Dict[str, Any], score_result: Dict[str, Any], use_llm: bool = False, mock: bool = False) -> str:
    # Provide a human-readable rationale. If LLM is available and requested, ask it.
    if mock or not use_llm or not OPENAI_API_KEY:
        # Build deterministic explanation
        parts = [f"Base score: {score_result['details'].get('base_score')}."]
        if score_result['details'].get('llm_applied'):
            parts.append("An LLM refinement was applied.")
        parts.append(f"Final score: {score_result['final_score']}.")
        return " ".join(parts)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"Applicant: {json.dumps(applicant)}\nScoreResult: {json.dumps(score_result)}\n\nWrite a concise human-friendly explanation (2-4 sentences) of why this final score was given."
        resp = client.chat.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
        text = resp.choices[0].message.content
        return text.strip()
    except Exception as e:
        return f"Could not generate LLM explanation: {e}"
