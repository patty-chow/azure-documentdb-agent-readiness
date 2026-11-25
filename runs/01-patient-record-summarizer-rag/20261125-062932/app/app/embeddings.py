import os
import random

EMBEDDING_DIM = 1536

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False


def _random_vector_for_text(text: str):
    # deterministic pseudo-random vector based on hash
    rnd = random.Random(abs(hash(text)) % (2**32))
    return [rnd.gauss(0, 1) for _ in range(EMBEDDING_DIM)]


def get_embedding(text: str):
    """Return an embedding for text. Uses OpenAI if OPENAI_API_KEY is present; otherwise returns a deterministic pseudo-random vector for demo/testing."""
    key = os.environ.get("OPENAI_API_KEY")
    if key and _OPENAI_AVAILABLE:
        openai.api_key = key
        resp = openai.Embedding.create(model="text-embedding-3-small", input=text)
        vec = resp["data"][0]["embedding"]
        return vec
    # deterministic pseudo-random fallback
    return _random_vector_for_text(text)
