import os
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.db import get_all_patients_with_last_visit

# For LLMs
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

# Care guidelines (context engineered) - simple illustrative rules
CARE_GUIDELINES = {
    "mammogram": {
        "description": "Women age 50-74 should have a mammogram every 2 years.",
        "gender": "F",
        "age_min": 50,
        "age_max": 74,
        "interval_days": 2 * 365
    },
    "colonoscopy": {
        "description": "Adults 50-75 should have colon cancer screening approximately every 10 years (or per alternate modalities).",
        "gender": None,
        "age_min": 50,
        "age_max": 75,
        "interval_days": 10 * 365
    },
    "diabetic_hba1c": {
        "description": "Patients with diabetes should have HbA1c at least once per year.",
        "gender": None,
        "diagnosis_required": "diabetes",
        "interval_days": 365
    }
}


def detect_gaps(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Given a list of patient dicts that include age, gender, diagnoses, and last_visit_date, return care gaps found per patient."""
    now = datetime.utcnow()
    results = []
    for p in patients:
        gaps = []
        for gap_key, rule in CARE_GUIDELINES.items():
            # filter by gender
            if rule.get("gender") and p.get("gender") != rule.get("gender"):
                continue
            if rule.get("age_min") and p.get("age") is not None:
                if p.get("age") < rule.get("age_min"):
                    continue
            if rule.get("age_max") and p.get("age") is not None:
                if p.get("age") > rule.get("age_max"):
                    continue
            if rule.get("diagnosis_required"):
                if rule.get("diagnosis_required") not in p.get("diagnoses", []):
                    continue
            # Determine last relevant date: use last_visit_date if present
            last = p.get("last_visit_date")
            needs = False
            reason = "no record of required screening"
            if last is None:
                needs = True
                reason = "no recorded visit"
            else:
                delta = now - last
                if delta.days > rule.get("interval_days"):
                    needs = True
                    reason = f"last visit {delta.days} days ago"
            if needs:
                gaps.append({"gap_type": gap_key, "rule": rule, "reason": reason})
        if gaps:
            results.append({"patient": p, "gaps": gaps})
    return results


def prioritise_and_generate_messages(gap_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Take detected gaps and use an LLM to prioritise and generate outreach talking points per gap type.

    Falls back to simple heuristics if OPENAI_API_KEY is not set.
    """
    # Simple heuristic priority: more gaps = higher priority; diabetes adds +1 priority; older age increases priority
    enriched = []
    for item in gap_results:
        p = item["patient"]
        num_gaps = len(item["gaps"]) if item.get("gaps") else 0
        priority = num_gaps * 10
        if "diabetes" in p.get("diagnoses", []):
            priority += 5
        age = p.get("age") or 0
        if age >= 65:
            priority += 3
        enriched.append({"patient": p, "gaps": item["gaps"], "priority_score": priority})

    # Sort descending
    enriched.sort(key=lambda x: x["priority_score"], reverse=True)

    if OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            # Build a prompt with care guidelines and the list of patients
            system = (
                "You are a clinical outreach assistant. Use the provided care guideline context and the patient list to:"
                " 1) confirm a priority ranking rationale for each patient, and 2) produce concise outreach talking points for each care gap."
            )
            user_content = (
                "Care guidelines:\n" + json.dumps(CARE_GUIDELINES, default=str, indent=2)
                + "\n\nPatients:\n" + json.dumps(enriched, default=str, indent=2)
                + "\n\nRespond with JSON array of objects like: [{\"patient_id\":..., \"priority_score\":..., \"rationale\":..., \"talking_points\":[...]}]"
            )
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ]
            resp = client.chat.create(model=OPENAI_MODEL, messages=messages)
            content = resp.choices[0].message.content
            try:
                out = json.loads(content)
            except Exception:
                # If LLM didn't return strict JSON, return heuristic output with raw text
                out = {"llm_text": content}
            return out
        except Exception as e:
            print(f"LLM call failed: {e}; falling back to templates.")

    # Fallback templated messages
    out = []
    for item in enriched:
        p = item["patient"]
        pts = []
        for g in item["gaps"]:
            t = f"Dear {p.get('name')}, Our records indicate you may be due for {g['gap_type']} as: {g['rule']['description']}. Reason: {g['reason']}. Please contact us to schedule."
            pts.append(t)
        out.append({"patient_id": p.get("_id"), "priority_score": item["priority_score"], "rationale": "heuristic", "talking_points": pts})
    return out


def run_end_to_end():
    patients = get_all_patients_with_last_visit()
    gaps = detect_gaps(patients)
    result = prioritise_and_generate_messages(gaps)
    return result
