import os
import time
from typing import Dict, Any, List

import openai

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = 1536
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

CLASSIFICATION_SYSTEM_PROMPT = (
    "You are a classifier for customer complaints. For the given complaint,"
    " return a JSON object with fields: product_category (one of: credit-card, mortgage, checking, savings, loan, other),"
    " root_cause (short text), urgency (low|medium|high). Only return JSON."
)

async def classify_text_with_llm(text: str) -> Dict[str, Any]:
    # Simple call to OpenAI ChatCompletion — wrapper for demonstration.
    prompt = CLASSIFICATION_SYSTEM_PROMPT + "\n\nComplaint:\n" + text
    resp = openai.ChatCompletion.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.0,
    )
    content = resp.choices[0].message.get("content", "")
    # Expecting JSON — attempt parse
    import json
    try:
        parsed = json.loads(content)
    except Exception:
        parsed = {"product_category": "other", "root_cause": content.strip(), "urgency": "low"}
    return parsed

async def embed_text(text: str) -> List[float]:
    # Call OpenAI embedding endpoint
    if not OPENAI_API_KEY:
        # Return dummy zeros for offline/test
        return [0.0] * EMBEDDING_DIMS
    resp = openai.Embedding.create(model=EMBEDDING_MODEL, input=text)
    vec = resp.data[0].embedding
    # Normalize for cosine if desired
    return vec

async def enrich_complaint(db_coll, complaint_doc):
    # complaint_doc is a Beanie document instance
    classification = await classify_text_with_llm(complaint_doc.complaint_text)
    embedding = await embed_text(complaint_doc.complaint_text)
    complaint_doc.product_category = classification.get("product_category")
    complaint_doc.root_cause = classification.get("root_cause")
    complaint_doc.urgency = classification.get("urgency")
    complaint_doc.embedding = embedding
    complaint_doc.classification_metadata = {"model": LLM_MODEL, "timestamp": time.time()}
    await complaint_doc.save()
    return complaint_doc
