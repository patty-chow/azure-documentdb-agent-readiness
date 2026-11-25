import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))


def _normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v.tolist()
    return (v / norm).tolist()


def embed_texts(texts):
    """Return list of embeddings for the given list of texts.

    If OPENAI_API_KEY is not set, return random normalized vectors for offline use.
    """
    if not OPENAI_API_KEY:
        # deterministic pseudo-random for reproducibility
        rng = np.random.default_rng(seed=42)
        return [_normalize(rng.standard_normal(EMBEDDING_DIMS)) for _ in texts]

    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=texts)
        embeddings = [d["embedding"] for d in resp["data"]]
        # normalize for cosine similarity
        return [_normalize(e) for e in embeddings]
    except Exception as e:
        # Fall back to random if embedding API fails
        rng = np.random.default_rng(seed=42)
        return [_normalize(rng.standard_normal(EMBEDDING_DIMS)) for _ in texts]


def embed_vector_from_features(features: dict):
    # For simplicity, stringify features and embed the string
    text = ", ".join(f"{k}:{v}" for k, v in sorted(features.items()))
    return embed_texts([text])[0]
