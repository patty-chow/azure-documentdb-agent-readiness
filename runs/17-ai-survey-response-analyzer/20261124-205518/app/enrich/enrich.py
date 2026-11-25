"""Enrichment pipeline using Beanie ODM. If OPENAI_API_KEY is present, uses OpenAI APIs for extraction and embeddings. Otherwise uses deterministic fallback logic so the sample can be run offline for verification."""
import os
import sys
import asyncio
from dotenv import load_dotenv

# ensure repo root on path so `from src` works when running scripts
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv()

from src.db import init_db
from src.models import SurveyResponse

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_MODEL_EMBEDDING", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))

# Light-weight fallback utilities
POSITIVE = {"love","great","excellent","good","intuitive","clean","reasonable","stable"}
NEGATIVE = {"slow","broke","confusing","complaints","bug","rollback","hotfix"}

import hashlib
import struct

async def fallback_extract(text: str):
    # themes: keywords found
    found = set()
    lowered = text.lower()
    for w in POSITIVE.union(NEGATIVE):
        if w in lowered:
            found.add(w)
    themes = list(found) if found else [lowered.split()[0]]
    # sentiment: naive score
    score = 0
    for w in POSITIVE:
        if w in lowered:
            score += 1
    for w in NEGATIVE:
        if w in lowered:
            score -= 1
    label = "neutral"
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    # representative quote: first sentence or truncated
    quote = text.split(".")[0].strip()
    if len(quote) > 200:
        quote = quote[:197] + "..."
    return themes, {"label": label, "score": float(score)}, quote

async def fallback_embedding(text: str):
    # deterministic pseudo-embedding derived from sha256 digest
    h = hashlib.sha256(text.encode("utf8")).digest()
    vec = []
    i = 0
    while len(vec) < EMBEDDING_DIMS:
        # consume 4 bytes into a float in range [-1,1]
        chunk = h[i % len(h):(i % len(h)) + 4]
        if len(chunk) < 4:
            chunk = chunk.ljust(4, b"\0")
        val = struct.unpack("I", chunk)[0]
        # normalize to [-1,1]
        vec.append(((val / 0xFFFFFFFF) * 2.0) - 1.0)
        i += 4
    return vec

# If OpenAI key exists, import the client
if OPENAI_API_KEY:
    import openai
    openai.api_key = OPENAI_API_KEY

    async def openai_extract(text: str):
        prompt = f"Extract up to 3 short themes (comma-separated), give a sentiment label (positive/neutral/negative) and a representative quote from the text:\n\nText: {text}\n\nRespond as JSON: {{\"themes\": [...], \"sentiment\": {{\"label\":..., \"score\":...}}, \"quote\": \"...\"}}"
        # Use the ChatCompletion for structured output (sync wrapper)
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL_CHAT", "gpt-4o-mini"),
            messages=[{"role":"user","content":prompt}],
            max_tokens=200,
            temperature=0.0,
        )
        import json
        # Attempt to parse assistant reply
        text_out = resp["choices"][0]["message"]["content"]
        try:
            data = json.loads(text_out)
            return data.get("themes", []), data.get("sentiment", {"label":"neutral","score":0.0}), data.get("quote", "")
        except Exception:
            return await fallback_extract(text)

    async def openai_embed(text: str):
        resp = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=text)
        return resp["data"][0]["embedding"]

else:
    openai_extract = None
    openai_embed = None

async def enrich_all(batch_size=20):
    client, db = await init_db()
    # find documents that are missing enrichment
    cursor = SurveyResponse.find({"themes": None}).sort("created_at")
    count = 0
    async for doc in cursor:
        text = doc.response_text
        if OPENAI_API_KEY and openai_extract:
            themes, sentiment, quote = await openai_extract(text)
            embedding = await openai_embed(text)
        else:
            themes, sentiment, quote = await fallback_extract(text)
            embedding = await fallback_embedding(text)
        # normalize embedding length
        if len(embedding) != EMBEDDING_DIMS:
            # try to pad/trim
            if len(embedding) > EMBEDDING_DIMS:
                embedding = embedding[:EMBEDDING_DIMS]
            else:
                embedding = embedding + [0.0] * (EMBEDDING_DIMS - len(embedding))
        doc.themes = themes
        doc.sentiment = sentiment
        doc.representative_quote = quote
        doc.embedding = embedding
        await doc.save()
        count += 1
    client.close()
    print(f"Enriched {count} documents.")

if __name__ == "__main__":
    asyncio.run(enrich_all())
