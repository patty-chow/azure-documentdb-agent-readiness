from datetime import datetime
from typing import Optional, List, Tuple

from pydantic import BaseModel, EmailStr, Field
from beanie import Document, PydanticObjectId


class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class Supplier(Document):
    name: str = Field(...)
    contact: Optional[ContactInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "suppliers"
        indexes = [
            "name",
        ]


class PurchaseOrder(Document):
    supplier_id: PydanticObjectId = Field(...)
    total_value: float = Field(..., gt=0)
    status: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "purchaseorders"
        indexes = [
            [("supplier_id", 1), ("status", 1)],
        ]
