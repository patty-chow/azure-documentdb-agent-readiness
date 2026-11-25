import os
from typing import List

import openai

MODEL_NAME = "text-embedding-3-small"  # 1536 dims


def _require_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required to compute embeddings")
    return api_key


def embed_text(text: str) -> List[float]:
    api_key = _require_api_key()
    openai.api_key = api_key
    # Optionally support Azure OpenAI via OPENAI_API_BASE
    api_base = os.environ.get("OPENAI_API_BASE")
    if api_base:
        openai.api_base = api_base
    resp = openai.Embeddings.create(model=MODEL_NAME, input=text)
    return resp.data[0].embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    api_key = _require_api_key()
    openai.api_key = api_key
    api_base = os.environ.get("OPENAI_API_BASE")
    if api_base:
        openai.api_base = api_base
    resp = openai.Embeddings.create(model=MODEL_NAME, input=texts)
    return [d.embedding for d in resp.data]
