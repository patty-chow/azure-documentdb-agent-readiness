import os
import math
import hashlib
import struct

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))


def _fake_embed(text: str, dims: int = EMBEDDING_DIMS):
    """Deterministic pseudo-embedding for offline testing.
    Produces a float vector by hashing chunks of the input. Not semantically meaningful but deterministic.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    # Expand hash into floats deterministically
    i = 0
    while len(vec) < dims:
        chunk = h[i % len(h): (i % len(h)) + 8]
        if len(chunk) < 8:
            chunk = (chunk + b"\x00" * 8)[:8]
        val = struct.unpack("!d", chunk)[0]
        vec.append(float(math.tanh(val)))
        i += 8
    return vec[:dims]


def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def get_embedding(text: str):
    """Get embedding either via OpenAI (if configured) or the fake fallback.
    Returns a normalized vector of EMBEDDING_DIMS floats.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key and _OPENAI_AVAILABLE:
        # Use the OpenAI python client if available
        client = OpenAI(api_key=api_key)
        model = EMBEDDING_MODEL
        resp = client.embeddings.create(model=model, input=text)
        vec = resp.data[0].embedding
        # Some providers already normalize; ensure normalization for COS similarity
        return normalize(vec)
    else:
        # Fallback deterministic embedding
        vec = _fake_embed(text, EMBEDDING_DIMS)
        return normalize(vec)


def generate_response_with_fallback(symptoms: str, contexts: list):
    """Deterministic reply generator used when LLM key is not set. Enforces guardrails.
    Returns a dict matching the expected structured response.
    """
    urgency = "low"
    for c in contexts:
        if c.get("documented_urgency") == "emergency":
            urgency = "emergency"
            break
        if c.get("documented_urgency") == "urgent":
            urgency = "urgent"
    advice = (
        "I am not a doctor. Based on the retrieved guideline excerpts, the recommended triage level is '" + urgency + "'. "
        "This is educational information only — always consult a qualified healthcare professional for medical advice. "
        "If you are experiencing severe or life-threatening symptoms, seek emergency care immediately."
    )

    sources = [
        {
            "section_id": c.get("section_id"),
            "title": c.get("title"),
            "snippet": c.get("text")[:240],
            "score": c.get("score")
        }
        for c in contexts
    ]

    return {"urgency": urgency, "advice": advice, "sources": sources}
