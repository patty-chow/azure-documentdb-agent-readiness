import os
import asyncio
import json
from datetime import datetime
from typing import List

import openai
from dotenv import load_dotenv

from .db import init_db
from .models import Review

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("MODEL", "gpt-3.5-turbo")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "8"))

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required in the environment to run the pipeline")
openai.api_key = OPENAI_API_KEY

async def analyze_review_text(text: str) -> dict:
    prompt = (
        "You are a JSON-only sentiment and theme extractor.\n"
        "Given the user's review text, return a JSON object with keys:\n"
        "- sentiment_label: one of ['positive','neutral','negative']\n"
        "- sentiment_score: float between 0.0 (negative) and 1.0 (positive)\n"
        "- themes: an array of short tags summarizing key themes (up to 6)\n\n"
        "Return ONLY valid JSON.\n\n"
        f"Review text:\n{text}\n"
    )
    try:
        resp = await openai.ChatCompletion.acreate(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            max_tokens=256,
            temperature=0.0,
        )
        content = resp.choices[0].message.content
        # Expect JSON; attempt to parse
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        # fallback: very simple rule-based heuristic
        score = 0.5
        label = "neutral"
        themes: List[str] = []
        txt = text.lower()
        if any(w in txt for w in ["love", "great", "excellent", "happy", "perfect"]):
            score = 0.9; label = "positive"; themes = ["praise"]
        elif any(w in txt for w in ["bad", "terrible", "awful", "disappointed", "poor"]):
            score = 0.1; label = "negative"; themes = ["complaint"]
        return {"sentiment_label": label, "sentiment_score": score, "themes": themes}

async def process_review(review: Review):
    result = await analyze_review_text(review.review_text)
    review.sentiment_score = float(result.get("sentiment_score", 0.5))
    review.sentiment_label = result.get("sentiment_label", "neutral")
    review.tags = result.get("themes", [])
    review.model_version = MODEL
    review.enriched_at = datetime.utcnow()
    await review.save()

async def run_pipeline():
    await init_db()
    semaphore = asyncio.Semaphore(CONCURRENCY)

    # find reviews missing sentiment_score
    cursor = Review.find({"sentiment_score": None})
    tasks = []
    async for review in cursor:
        async def sem_task(r=review):
            async with semaphore:
                try:
                    await process_review(r)
                    print(f"Enriched review {r.review_id}")
                except Exception as e:
                    print(f"Failed to enrich {r.review_id}: {e}")
        tasks.append(asyncio.create_task(sem_task()))
    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("No reviews to process")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
