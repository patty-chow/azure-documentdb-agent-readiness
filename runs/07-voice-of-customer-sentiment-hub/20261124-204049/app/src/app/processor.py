import os
import json
from typing import List, Dict, Any
from datetime import datetime

# Simple heuristic-based analysis and deterministic embedding for offline verification
POS_WORDS = {"good","great","love","excellent","happy","satisfied","awesome","like","amazing","helpful","resolved"}
NEG_WORDS = {"bad","terrible","hate","poor","angry","unsatisfied","disappointed","issue","problem","crash","error","bug","frustrated"}

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

def heuristic_extract(text: str) -> Dict[str, Any]:
    words = {w.strip('.,!?').lower() for w in text.split()}
    pos = len(words & POS_WORDS)
    neg = len(words & NEG_WORDS)
    score = 0.0
    if pos + neg > 0:
        score = (pos - neg) / (pos + neg)
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    topics = [w for w in words if len(w) > 6][:3]
    quote = text[:200]
    return {"sentiment_score": score, "sentiment_label": label, "topics": topics, "quote": quote}


def deterministic_embedding(text: str) -> List[float]:
    import hashlib
    h = hashlib.sha256(text.encode('utf-8')).digest()
    v = [((b % 200) - 100) / 100.0 for b in h]
    if len(v) < EMBEDDING_DIM:
        v = (v * ((EMBEDDING_DIM // len(v)) + 1))[:EMBEDDING_DIM]
    else:
        v = v[:EMBEDDING_DIM]
    return v

def analyze_and_prepare(feedback_item: Dict[str, Any]) -> Dict[str, Any]:
    text = feedback_item.get('text', '')
    analysis = heuristic_extract(text)
    embedding = deterministic_embedding(text)
    doc = {
        'channel': feedback_item.get('channel', 'unknown'),
        'text': text,
        'timestamp': feedback_item.get('timestamp') or datetime.utcnow(),
        'sentiment_score': float(analysis.get('sentiment_score', 0.0)),
        'sentiment_label': analysis.get('sentiment_label', 'neutral'),
        'topics': analysis.get('topics', []),
        'quote': analysis.get('quote', text[:200]),
        'embedding': embedding,
    }
    return doc
