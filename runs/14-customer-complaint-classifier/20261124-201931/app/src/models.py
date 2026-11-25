from typing import List, Optional
from datetime import datetime
from beanie import Document, Indexed
from pydantic import BaseModel, Field

class ClassificationMetadata(BaseModel):
    model: Optional[str]
    timestamp: Optional[datetime]

class Complaint(Document):
    external_id: str = Field(..., description="Unique external id for idempotent seed upserts")
    complaint_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    customer_id: Optional[str]

    product_category: Optional[str] = None
    root_cause: Optional[str] = None
    urgency: Optional[str] = None

    embedding: Optional[List[float]] = None
    embedding_dimensions: Optional[int] = None

    classification_metadata: Optional[ClassificationMetadata] = None

    class Settings:
        name = "complaints"
        # Add default indexes via Beanie if desired; we will create specialized indexes via the MCP server

    class Config:
        schema_extra = {
            "example": {
                "external_id": "seed-1",
                "complaint_text": "I was charged an unexpected fee on my account",
                "customer_id": "cust-123",
            }
        }
