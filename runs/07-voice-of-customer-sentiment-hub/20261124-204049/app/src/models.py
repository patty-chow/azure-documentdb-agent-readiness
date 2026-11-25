from beanie import Document
from pydantic import Field
from typing import List, Optional
from datetime import datetime

class Feedback(Document):
    channel: str
    source_id: Optional[str] = None
    text: str
    sentiment: Optional[float] = None
    topics: Optional[List[str]] = None
    quote: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Collection:
        name = "feedback"
