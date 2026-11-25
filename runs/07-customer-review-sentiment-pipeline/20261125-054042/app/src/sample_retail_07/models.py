from typing import List, Optional
from datetime import datetime
from beanie import Document
from pymongo import ASCENDING, DESCENDING
from pymongo.operations import IndexModel

class Review(Document):
    review_id: str
    product_id: str
    user_id: str
    review_text: str
    created_at: datetime
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    tags: Optional[List[str]] = None
    model_version: Optional[str] = None
    enriched_at: Optional[datetime] = None

    class Settings:
        name = "reviews"
        indexes = [
            IndexModel([("product_id", ASCENDING)]),
            IndexModel([("product_id", ASCENDING), ("sentiment_score", DESCENDING)]),
        ]
