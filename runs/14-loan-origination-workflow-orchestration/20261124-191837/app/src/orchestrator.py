import asyncio
from datetime import datetime
from typing import List
from beanie import PydanticObjectId
from .models import LoanApplication, Transition
from .db import init_db, close_client
from .agents import UnderwritingAgent, ComplianceAgent, StubLLM
import os

# Orchestrator logic
class Orchestrator:
    def __init__(self, underwriting_agent: UnderwritingAgent, compliance_agent: ComplianceAgent):
        self.underwriting_agent = underwriting_agent
        self.compliance_agent = compliance_agent

    async def advance(self, app_id: PydanticObjectId):
        # Load current doc
        doc = await LoanApplication.get(app_id)
        if not doc:
            raise ValueError("Application not found")

        if doc.current_state == "submitted":
            decision = self.underwriting_agent.decide(doc.applicant.dict())
            new_state = "underwriting" if decision == "continue" else ("rejected" if decision == "reject" else "underwriting")
            # For demo, underwriting agent decides approve/reject; we'll move to underwriting then compliance
            await self._transition_atomic(app_id, expected_state="submitted", new_state="underwriting", agent="underwriting", decision=decision)
            doc = await LoanApplication.get(app_id)

        if doc.current_state == "underwriting":
            # Underwriting makes final decision to approve or send to compliance
            decision = self.underwriting_agent.decide(doc.applicant.dict())
            if decision == "reject":
                await self._transition_atomic(app_id, expected_state="underwriting", new_state="rejected", agent="underwriting", decision=decision)
                return
            else:
                await self._transition_atomic(app_id, expected_state="underwriting", new_state="compliance", agent="underwriting", decision=decision)

        doc = await LoanApplication.get(app_id)
        if doc.current_state == "compliance":
            decision = self.compliance_agent.decide(doc.applicant.dict())
            if decision == "reject":
                await self._transition_atomic(app_id, expected_state="compliance", new_state="rejected", agent="compliance", decision=decision)
            else:
                await self._transition_atomic(app_id, expected_state="compliance", new_state="approved", agent="compliance", decision=decision)

    async def _transition_atomic(self, app_id, expected_state: str, new_state: str, agent: str, decision: str):
        # Perform a find_one_and_update filter-on-state and $push the transition
        from motor.motor_asyncio import AsyncIOMotorClient
        from .db import get_client
        client: AsyncIOMotorClient = await get_client()
        db = client.get_database("sample_fintech_14")
        coll = db.get_collection("loan_applications")

        transition = {
            "previous_state": expected_state,
            "new_state": new_state,
            "agent": agent,
            "decision": decision,
            "timestamp": datetime.utcnow()
        }

        res = await coll.find_one_and_update(
            {"_id": app_id, "current_state": expected_state},
            {"$set": {"current_state": new_state}, "$push": {"transitions": transition}},
            return_document=False
        )
        if res is None:
            raise RuntimeError(f"Failed to transition {app_id} from {expected_state} to {new_state} -- state mismatch or missing document")

async def create_orchestrator():
    # Choose LLM: use OPENAI if present else stub
    from .agents import StubLLM
    llm = StubLLM()
    underwriting = UnderwritingAgent(llm)
    compliance = ComplianceAgent(llm)
    return Orchestrator(underwriting, compliance)

async def run_for_demo(app_id):
    # Initialize DB and run orchestrator
    await init_db([LoanApplication])
    orch = await create_orchestrator()
    await orch.advance(app_id)
    await close_client()
