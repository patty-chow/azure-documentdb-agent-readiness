from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class RawNote(Document):
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "raw_notes"

class DeidNote(Document):
    text: str
    sourceId: str = Indexed()
    deid_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tool_version: Optional[str] = None

    class Settings:
        name = "deid_notes"
