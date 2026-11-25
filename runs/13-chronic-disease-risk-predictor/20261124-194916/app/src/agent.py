import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def generate_narrative(prompt: str, retrieved_profiles: list):
    """Generate a personalised narrative using OpenAI via a simple prompt.

    If OPENAI_API_KEY is not set, return a deterministic template combining retrieved_profiles.
    """
    if not OPENAI_API_KEY:
        # Simple deterministic narrative for offline demo
        lines = ["Personalised risk summary (offline mode):"]
        for p in retrieved_profiles:
            lines.append(f"- Similar profile {p.get('patient_id')} (score={p.get('score'):.3f}): risk={p.get('risk_label')}")
        lines.append("Recommended interventions: See aggregated recommendations below.")
        # aggregate top recommendations
        recs = []
        for p in retrieved_profiles:
            recs.extend(p.get("recommended_interventions", []))
        unique = sorted(set(recs))
        lines.append("Aggregated interventions: " + ", ".join(unique[:10]))
        return "\n".join(lines)

    # Use OpenAI chat completion for narrative
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        system_prompt = "You are a clinical-risk assistant that writes short personalised narratives and suggested interventions based on similar patient profiles. Be clear and concise."
        user_prompt = prompt + "\n\nNearby profiles:\n" + "\n".join(
            [f"- id:{p.get('patient_id')}, risk:{p.get('risk_label')}, interventions:{p.get('recommended_interventions')} (score={p.get('score'):.3f})" for p in retrieved_profiles]
        )
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(LLM error: {e})"
