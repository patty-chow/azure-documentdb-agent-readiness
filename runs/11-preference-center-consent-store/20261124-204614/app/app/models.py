from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class HistoryItem(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str  # 'grant' or 'withdraw'
    channels: Dict[str, bool]
    version: int
    actor: Optional[str] = None
    reason: Optional[str] = None

class Consent(Document):
    customerId: Indexed(str)  # logical key
    consentVersion: int = 0
    channels: Dict[str, bool] = Field(default_factory=dict)
    history: List[HistoryItem] = Field(default_factory=list)
    retention_expires_at: Optional[datetime] = None

    class Collection:
        name = "consents"

    class Settings:
        name = "consents"
