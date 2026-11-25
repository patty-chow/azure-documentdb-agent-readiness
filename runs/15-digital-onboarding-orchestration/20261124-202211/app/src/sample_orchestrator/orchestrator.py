import asyncio
from typing import List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from .db import get_client, get_db_name
from .models import OnboardingApplication, Transition
from . import agents


AGENTS = [
    ("id_verification", agents.id_verification_agent),
    ("risk_assessment", agents.risk_assessment_agent),
    ("account_opening", agents.account_opening_agent),
]


async def orchestrate(application_id: str) -> dict:
    client: AsyncIOMotorClient = get_client()
    db_name = get_db_name()
    coll_name = OnboardingApplication.Settings.name
    coll = client[db_name][coll_name]

    # Load current document
    app_doc = await coll.find_one({"applicant_id": application_id})
    if not app_doc:
        raise RuntimeError(f"Application {application_id} not found")

    # run agents sequentially, applying atomic updates in transactions
    for agent_name, agent_fn in AGENTS:
        # run agent to determine next state
        new_state, message = await agent_fn(app_doc)
        from_state = app_doc.get("state")
        transition = {
            "agent": agent_name,
            "from_state": from_state,
            "to_state": new_state,
            "ts": datetime.utcnow(),
        }

        # perform atomic update inside a session transaction
        async with await client.start_session() as session:
            async with session.start_transaction():
                updated = await coll.find_one_and_update(
                    {"applicant_id": application_id},
                    {"$set": {"state": new_state}, "$push": {"history": transition}},
                    upsert=False,
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )
        app_doc = updated
        # log transition to console (sample logging)
        print(f"Transitioned {application_id}: {from_state} -> {new_state} by {agent_name} : {message}")

        if new_state == "FAILED":
            break

    return app_doc
