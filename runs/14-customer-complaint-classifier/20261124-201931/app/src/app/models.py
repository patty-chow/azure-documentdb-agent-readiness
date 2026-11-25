from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, List, Dict

class Complaint(Document):
    external_id: str = Field(..., description="External unique id for idempotent upserts")
    complaint_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    customer_id: Optional[str] = None
    product_category: Optional[str] = None
    root_cause: Optional[str] = None
    urgency: Optional[str] = None
    embedding: Optional[List[float]] = None
    classification_metadata: Optional[Dict] = None

    class Settings:
        name = "complaints"
