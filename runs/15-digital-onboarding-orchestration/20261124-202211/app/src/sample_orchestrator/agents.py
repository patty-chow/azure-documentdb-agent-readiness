import asyncio
from typing import Tuple

# Simple, deterministic agents for the sample. In a real app these would call LLMs
# or external services. Each returns (new_state, log_message).


async def id_verification_agent(application: dict) -> Tuple[str, str]:
    # fake check: if name contains 'fail' -> fail
    await asyncio.sleep(0.1)
    name = application.get("applicant_name", "")
    if "fail" in name.lower():
        return "FAILED", "ID verification failed"
    return "ID_VERIFIED", "ID verified"


async def risk_assessment_agent(application: dict) -> Tuple[str, str]:
    await asyncio.sleep(0.1)
    # very simple risk check: applicant_id ending with 9 is high risk
    aid = application.get("applicant_id", "")
    if aid.endswith("9"):
        return "FAILED", "High risk detected"
    return "RISK_ASSESSED", "Risk acceptable"


async def account_opening_agent(application: dict) -> Tuple[str, str]:
    await asyncio.sleep(0.1)
    # if name contains 'slow' simulate an external transient failure
    name = application.get("applicant_name", "")
    if "slow" in name.lower():
        return "FAILED", "Account opening service error"
    return "ACCOUNT_OPENED", "Account opened successfully"
