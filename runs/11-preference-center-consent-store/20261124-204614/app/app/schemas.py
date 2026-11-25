from pydantic import BaseModel
from typing import Dict, Optional

class RecordConsentRequest(BaseModel):
    customerId: str
    channels: Dict[str, bool]
    actor: Optional[str] = None
    reason: Optional[str] = None

class WithdrawConsentRequest(BaseModel):
    customerId: str
    channels: Optional[Dict[str, bool]] = None
    actor: Optional[str] = None
    reason: Optional[str] = None

class ConsentResponse(BaseModel):
    customerId: str
    consentVersion: int
    channels: Dict[str, bool]
