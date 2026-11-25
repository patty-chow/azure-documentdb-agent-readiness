# Lightweight model helpers (no Beanie) - documents are plain dicts stored in the collection
from datetime import datetime
from typing import List, Optional

# This module documents the expected shape of a feedback document used by the sample.
# Documents are stored in the 'feedbacks' collection with these keys:
# channel, text, timestamp, sentiment_score, sentiment_label, topics, quote, embedding

def make_feedback_doc(channel: str, text: str, timestamp: Optional[datetime]=None, sentiment_score: float=0.0, sentiment_label: str='neutral', topics: Optional[List[str]]=None, quote: Optional[str]=None, embedding: Optional[List[float]]=None):
    return {
        'channel': channel,
        'text': text,
        'timestamp': timestamp if timestamp else datetime.utcnow(),
        'sentiment_score': float(sentiment_score),
        'sentiment_label': sentiment_label,
        'topics': topics or [],
        'quote': quote,
        'embedding': embedding,
    }
