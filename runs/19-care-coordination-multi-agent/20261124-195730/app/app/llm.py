import os
from typing import Dict, Any

# Lightweight wrapper: use OpenAI if API key present, otherwise raise when called

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))


def synthesise_care_plan(sources: Dict[str, Any], patient_id: str) -> str:
    """Synthesize a care plan text from the collected sources. If OPENAI_API_KEY is not
    present this returns a simple deterministic template for tests and demos."""
    if not OPENAI_KEY:
        # Return a deterministic template so sample runs work without an LLM
        lines = [f"Care plan for {patient_id}:\n"]
        if sources.get("primary_care_notes"):
            lines.append("Primary care summary:\n")
            for n in sources["primary_care_notes"]:
                lines.append(f"- {n.get('note', '')}\n")
        if sources.get("referrals"):
            lines.append("Referrals:\n")
            for r in sources["referrals"]:
                lines.append(f"- {r.get('note', '')} (to {r.get('specialty')})\n")
        if sources.get("medications"):
            lines.append("Medications:\n")
            for m in sources["medications"]:
                lines.append(f"- {m.get('name')} {m.get('dose', '')} {m.get('schedule','')}\n")
        lines.append("\nPlan:\n- Follow-up in 2 weeks.\n")
        return "\n".join(lines)

    # If OPENAI_KEY is present, use a simple OpenAI completion via requests to keep deps light
    # We avoid importing the OpenAI SDK directly to keep behaviour explicit in tests.
    import openai
    openai.api_key = OPENAI_KEY
    prompt = """
    You are a clinical summarization assistant. Given the following JSON sources, produce a concise care plan.
    Sources:
    """
    import json
    prompt += json.dumps(sources, indent=2)
    prompt += f"\n\nProduce a concise care plan for patient {patient_id}."
    resp = openai.ChatCompletion.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=[{"role":"user", "content": prompt}],
        max_tokens=512,
        temperature=0.2,
    )
    return resp.choices[0].message.content
