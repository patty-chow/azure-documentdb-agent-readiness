from beanie import Document
from pydantic import Field, validator
from datetime import date, datetime
from typing import Optional, Dict, Any

class SwiftMessage(Document):
    message_id: Optional[str]
    message_type: str = Field(..., description="MT103 or MT202")
    sender: Optional[str]
    receiver: Optional[str]
    value_date: Optional[date]
    amount: Optional[float]
    currency: Optional[str]
    raw_text: str
    parsed: Optional[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "swift_messages"
        # additional indexes can be created at startup

    @validator("message_type")
    def message_type_must_be_known(cls, v):
        if v not in ("MT103", "MT202"):
            raise ValueError("message_type must be MT103 or MT202")
        return v

    @validator("amount")
    def amount_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("amount must not be negative")
        return v
