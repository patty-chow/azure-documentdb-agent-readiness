from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional

class LabResult(Document):
    patientId: str = Indexed(str)
    testCode: str = Indexed(str)
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "lab_results"
