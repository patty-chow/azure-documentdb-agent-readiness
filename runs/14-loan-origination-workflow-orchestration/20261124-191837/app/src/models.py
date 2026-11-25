from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Applicant(BaseModel):
    name: str
    ssn_last4: Optional[str]
    credit_score: Optional[int]
    requested_amount: Optional[float]

class Transition(BaseModel):
    previous_state: str
    new_state: str
    agent: str
    decision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LoanApplication(Document):
    current_state: Indexed(str)  # index on current_state
    applicant: Applicant
    transitions: List[Transition] = []

    class Collection:
        name = "loan_applications"

    # Helper: render a summary
    def summary(self) -> str:
        return f"LoanApplication(id={self.id}, state={self.current_state}, applicant={self.applicant.name})"
