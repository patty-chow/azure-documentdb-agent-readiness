from typing import List, Optional
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field


class Transition(BaseModel):
    agent: str
    from_state: str
    to_state: str
    ts: datetime = Field(default_factory=datetime.utcnow)


class OnboardingApplication(Document):
    applicant_id: str
    applicant_name: str
    state: str = "INIT"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    history: List[Transition] = Field(default_factory=list)
    schemaVersion: int = 1

    class Settings:
        name = "onboarding_applications"
