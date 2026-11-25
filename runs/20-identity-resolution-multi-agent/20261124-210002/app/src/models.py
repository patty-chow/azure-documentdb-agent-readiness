from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SourceMeta(BaseModel):
    source: str
    raw: Dict[str, Any] = Field(default_factory=dict)

class ProfileData(BaseModel):
    name: Optional[str] = None
    emails: Optional[List[str]] = Field(default_factory=list)
    phones: Optional[List[str]] = Field(default_factory=list)
    address: Optional[str] = None
    embedding: Optional[List[float]] = None
    source: Optional[SourceMeta] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Profile(Document):
    name: Optional[str] = None
    emails: Optional[List[str]] = Field(default_factory=list)
    phones: Optional[List[str]] = Field(default_factory=list)
    address: Optional[str] = None
    embedding: Optional[List[float]] = None
    source: Optional[SourceMeta] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"

class GoldenRecord(Document):
    merged: Dict[str, Any]
    provenance: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "golden_profiles"

class AuditEntry(Document):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    merged_ids: List[str]
    confidence: float
    source_docs: List[Dict[str, Any]]
    note: Optional[str] = None

    class Settings:
        name = "merge_audits"
