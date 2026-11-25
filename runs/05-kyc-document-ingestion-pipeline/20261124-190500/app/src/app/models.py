from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ExtractedEntities(BaseModel):
    name: Optional[str]
    dob: Optional[str]
    address: Optional[str]
    government_id: Optional[str]
    raw: Dict[str, Any] = Field(default_factory=dict)

class Customer(Document):
    name: Optional[str]
    dob: Optional[str]
    address: Optional[str]
    government_id: Optional[Indexed(str, unique=True)]
    extracted: ExtractedEntities
    status: str = "manual_review"  # or "complete"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Collection:
        name = "customers"

    def set_complete_if_valid(self):
        # Simple completeness heuristic
        if self.name and self.dob and self.government_id and self.address:
            self.status = "complete"
        else:
            self.status = "manual_review"

    async def upsert(self):
        # Upsert by government_id
        if not self.government_id:
            # No stable key -> always insert as manual review
            await self.insert()
            return
        await self.replace_one({'government_id': self.government_id}, self, upsert=True)
