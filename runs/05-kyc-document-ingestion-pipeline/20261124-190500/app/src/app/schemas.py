from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ExtractionSchema(BaseModel):
    name: Optional[str]
    dob: Optional[str]
    address: Optional[str]
    government_id: Optional[str]
    # additional raw content to preserve
    raw: Dict[str, Any] = Field(default_factory=dict)

    def is_complete(self):
        return bool(self.name and self.dob and self.address and self.government_id)
