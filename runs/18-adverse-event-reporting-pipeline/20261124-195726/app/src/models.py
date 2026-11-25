from datetime import datetime, date
from typing import Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field

class AdverseEvent(Document):
    drug: str = Field(..., description="Drug name")
    event: str = Field(..., description="Adverse event description")
    severity: Optional[str] = Field(None, description="Severity (e.g. mild/moderate/severe)")
    onset_date: Optional[date] = Field(None, description="Onset date, ISO format")
    raw_text: Optional[str] = Field(None, description="Original free-text report")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Collection:
        name = "adverse_events"

    class Settings:
        # Beanie will create indexes declared here during init
        # We still create a compound index programmatically at startup for clarity
        pass
