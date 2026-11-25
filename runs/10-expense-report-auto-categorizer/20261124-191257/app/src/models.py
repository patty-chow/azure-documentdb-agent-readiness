from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Item(BaseModel):
    item_id: str
    date: datetime
    merchant: str
    amount: float
    description: Optional[str] = None
    category: Optional[str] = None
    policy_violation: Optional[bool] = False
    violation_reason: Optional[str] = None

class Report(Document):
    report_id: str = Field(...)
    status: str = Field(default="submitted", description="submitted|processed")
    submitter: Optional[str] = None
    items: List[Item] = Field(default_factory=list)
    schema_version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "expense_reports"
        # allow indexing the status field for faster lookups (Beanie will create indexes via separate calls if needed)
        bson_encoders = {datetime: lambda dt: dt.isoformat()}
