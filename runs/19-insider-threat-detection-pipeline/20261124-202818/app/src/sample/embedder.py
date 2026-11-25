import os
from typing import List
import openai
from .config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, EMBEDDING_DIMS

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def embed_text(text: str) -> List[float]:
    """Call OpenAI embeddings API and return a vector."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    resp = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    vec = resp["data"][0]["embedding"]
    if len(vec) != EMBEDDING_DIMS:
        # warn but still return
        print(f"Warning: embedding dim {len(vec)} != expected {EMBEDDING_DIMS}")
    return vec


def embed_features_as_text(features: list) -> List[float]:
    # For simplicity, we stringify the features into a stable text representation
    # and embed that.
    text = "features:" + ",".join([f"{x:.6f}" for x in features])
    return embed_text(text)
