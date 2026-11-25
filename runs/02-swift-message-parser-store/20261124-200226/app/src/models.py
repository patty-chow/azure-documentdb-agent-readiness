from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from beanie import Document

class SwiftMessage(Document):
    message_id: str = Field(..., description="SWIFT transaction reference (:20:)")
    message_type: str = Field(..., description="MT type, e.g., MT103 or MT202")
    raw_text: str = Field(..., description="Original raw message")

    sender: Optional[str]
    receiver: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    value_date: Optional[date]
    parsed: Optional[Dict[str, Any]] = None

    class Settings:
        name = "swift_messages"

    class Config:
        schema_extra = {
            "example": {
                "message_id": "ABC123",
                "message_type": "MT103",
                "raw_text": "MT103|:20:ABC123|:32A:240101USD1234.56|:50K:/12345\\nJOHN DOE",
            }
        }


class ParsedSwift(BaseModel):
    message_id: str
    message_type: str
    sender: Optional[str]
    receiver: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    value_date: Optional[date]
    parsed: Dict[str, Any]

    @validator("message_type")
    def mt_upper(cls, v):
        return v.upper()
