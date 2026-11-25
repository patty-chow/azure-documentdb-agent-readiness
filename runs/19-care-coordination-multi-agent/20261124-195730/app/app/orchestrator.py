import os
from typing import Dict, Any
from .agents import get_patient_record, get_referrals, get_medications, write_care_plan

# Use OpenAI for synthesis if available
try:
    import openai
except Exception:
    openai = None


def synthesize_care_plan_with_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """Call the LLM (OpenAI) to synthesise a care plan. Falls back to a simple template if no API key."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not openai:
        # Fallback simple synthesiser
        return {
            "summary": f"Care plan (fallback) for {context.get('patient', {}).get('patient_id')}",
            "recommendations": [
                "Follow up with primary care in 2 weeks",
                "Review medications with pharmacy",
            ],
            "sections": {
                "primary_care_notes": context.get("patient", {}).get("notes", ""),
                "referrals": [r.get("note") for r in context.get("referrals", [])],
                "medications": [m.get("medication") for m in context.get("medications", [])]
            }
        }

    openai.api_key = api_key
    if os.environ.get("OPENAI_API_BASE"):
        openai.api_base = os.environ.get("OPENAI_API_BASE")

    messages = [
        {"role": "system", "content": "You are a clinical summarisation assistant. Produce a clear, concise care plan."},
        {"role": "user", "content": f"Patient record:\n{context.get('patient')}\n\nReferrals:\n{context.get('referrals')}\n\nMedications:\n{context.get('medications')}\n\nPlease synthesise a care plan as JSON with summary, recommendations (list), and sections."}
    ]

    resp = openai.ChatCompletion.create(
        model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=messages,
        max_tokens=800,
        temperature=0.2,
    )

    # Try to parse JSON out of the assistant's reply; if not possible, return text in summary
    content = resp.choices[0].message.get("content", "")
    try:
        import json
        parsed = json.loads(content)
        return parsed
    except Exception:
        return {"summary": content}


def orchestrate_and_write(patient_id: str) -> Dict[str, Any]:
    patient = get_patient_record(patient_id)
    referrals = get_referrals(patient_id)
    medications = get_medications(patient_id)

    context = {
        "patient": patient,
        "referrals": referrals,
        "medications": medications,
    }

    plan = synthesize_care_plan_with_llm(context)
    inserted_id = write_care_plan(patient_id, plan)
    return {"care_plan_id": inserted_id, "care_plan": plan}
