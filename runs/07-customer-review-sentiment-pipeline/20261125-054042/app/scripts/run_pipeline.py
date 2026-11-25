#!/usr/bin/env python3
"""Run the enrichment pipeline: load reviews missing sentiment, call OpenAI (or mock) to classify and extract themes, and upsert back to DocumentDB using Beanie.
"""
import os
import sys
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from src.sample_retail_07.db import init_db
from src.sample_retail_07.models import Review

OPENAI_KEY_ENV = "OPENAI_API_KEY"
OPENAI_CONCURRENCY_ENV = "OPENAI_CONCURRENCY"
MODEL = "gpt-3.5-turbo"

async def call_openai_for_review(review_text: str) -> Dict[str, Any]:
    """Call OpenAI Chat Completions API to get sentiment and themes.
    Expects the model to return a JSON object in the assistant content, e.g.
    {"sentiment_label":"positive","sentiment_score":0.87,"themes":["price","quality"]}
    """
    api_key = os.getenv(OPENAI_KEY_ENV)
    if not api_key:
        # Mock deterministic fallback
        text = review_text.lower()
        score = 0.5
        if any(w in text for w in ["great","excellent","happy","five stars","good"]):
            score = 0.9
            label = "positive"
        elif any(w in text for w in ["terrible","broke","poor","not recommend","unhappy","disappointed"]):
            score = 0.1
            label = "negative"
        else:
            score = 0.5
            label = "neutral"
        themes = []
        for term in ["price","quality","shipping","packaging","reliability"]:
            if term in text:
                themes.append(term)
        return {"sentiment_label": label, "sentiment_score": score, "themes": themes}

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    system = "You are a JSON-only assistant. Respond with a single JSON object (no surrounding text). Keys: sentiment_label (positive|neutral|negative), sentiment_score (float 0..1), themes (array of short strings)."
    user = f"Classify sentiment and extract up to 5 themes from this product review: {review_text}"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": 200,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # extract assistant content
        content = data["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except Exception:
            # best-effort: find first JSON substring
            import re
            m = re.search(r"\{.*\}", content, flags=re.S)
            if m:
                parsed = json.loads(m.group(0))
            else:
                raise
        return parsed


async def enrich_review(review: Review) -> None:
    parsed = await call_openai_for_review(review.review_text)
    # Map and validate
    sentiment_score = float(parsed.get("sentiment_score", 0.5))
    sentiment_label = parsed.get("sentiment_label") or ("positive" if sentiment_score>0.6 else "negative" if sentiment_score<0.4 else "neutral")
    themes = parsed.get("themes") or []
    review.sentiment_score = sentiment_score
    review.sentiment_label = sentiment_label
    review.tags = themes
    review.model_version = MODEL
    review.enriched_at = datetime.utcnow()
    await review.save()


async def run_pipeline(concurrency: int = 5):
    await init_db()
    # find reviews with missing sentiment_score
    cursor = Review.find(Review.sentiment_score == None)
    reviews = await cursor.to_list()
    print(f"Found {len(reviews)} reviews to process")
    sem = asyncio.Semaphore(concurrency)
    async def worker(r: Review):
        async with sem:
            try:
                await enrich_review(r)
                print(f"Enriched {r.review_id}")
            except Exception as e:
                print(f"Failed to enrich {r.review_id}: {e}")
    await asyncio.gather(*(worker(r) for r in reviews))

if __name__ == "__main__":
    c = int(os.getenv(OPENAI_CONCURRENCY_ENV, "5"))
    asyncio.run(run_pipeline(concurrency=c))
