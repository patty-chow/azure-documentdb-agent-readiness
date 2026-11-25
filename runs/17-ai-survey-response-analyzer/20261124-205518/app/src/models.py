from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Sentiment(BaseModel):
    label: str
    score: float

class SurveyResponse(Document):
    survey_id: str = Indexed()
    question_id: str = Indexed()
    respondent_id: Optional[str]
    response_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Enrichment fields
    themes: Optional[List[str]] = None
    sentiment: Optional[Dict[str, Any]] = None
    representative_quote: Optional[str] = None
    embedding: Optional[List[float]] = None

    schema_version: int = 1

    class Settings:
        name = "survey_responses"
        use_state_management = False
