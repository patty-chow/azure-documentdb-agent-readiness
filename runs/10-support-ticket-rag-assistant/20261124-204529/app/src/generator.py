import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
if OPENAI_API_BASE:
    openai.api_base = OPENAI_API_BASE


def generate_suggestion(ticket_text, contexts, max_tokens=256):
    """Call OpenAI chat completion to generate a concise suggested resolution.
    contexts: list of dicts {title, content}
    """
    if not OPENAI_API_KEY:
        # Fallback deterministic template
        combined = "\n---\n".join([f"{c['title']}: {c['content']}" for c in contexts])
        return f"Suggested resolution (template): Based on {len(contexts)} similar items. Ticket: {ticket_text[:120]}\nContext:\n{combined[:800]}\nAction: Investigate logs and restart service."

    prompt = (
        "You are a helpful support assistant. Given a user ticket and several past resolutions or KB articles,\n"
        "generate a concise suggested resolution limited to 3 sentences. Use only the provided context and do not invent facts.\n"
        "Ticket:\n" + ticket_text + "\n\nContext items:\n"
    )
    for i, c in enumerate(contexts, 1):
        prompt += f"{i}. {c.get('title','no-title')}: {c.get('content','')[:500]}\n"

    # Use Chat Completions if available
    resp = openai.ChatCompletion.create(
        model=OPENAI_API_CHAT_MODEL if False else OPENAI_CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    text = resp["choices"][0]["message"]["content"].strip()
    return text
