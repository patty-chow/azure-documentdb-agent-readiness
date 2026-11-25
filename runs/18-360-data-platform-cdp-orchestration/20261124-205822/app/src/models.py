from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

@dataclass
class CustomerRecord:
    email: str
    name: str
    normalized_name: str = ""
    addresses: List[Dict[str, Any]] = field(default_factory=list)
    firmographics: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)
    schemaVersion: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "email": self.email,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "addresses": self.addresses,
            "firmographics": self.firmographics,
            "embedding": self.embedding,
            "schemaVersion": self.schemaVersion,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
