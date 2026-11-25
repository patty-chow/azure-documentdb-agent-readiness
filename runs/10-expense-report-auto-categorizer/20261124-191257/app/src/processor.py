import os
import asyncio
from typing import Dict, Any
from beanie import PydanticObjectId
from pydantic import BaseModel
from .models import Report, Item


class SessionMemory:
    """Simple in-memory mapping to keep consistent categorizations during a run."""
    def __init__(self):
        self.merchant_to_category: Dict[str, str] = {}

    def get(self, merchant: str):
        return self.merchant_to_category.get(merchant)

    def set(self, merchant: str, category: str):
        self.merchant_to_category[merchant] = category


async def classify_item(item: Item, memory: SessionMemory, use_ai: bool = True) -> Dict[str, Any]:
    # First consult session memory for the merchant
    mem = memory.get(item.merchant)
    if mem:
        return {"category": mem, "policy_violation": False, "violation_reason": None}

    if use_ai and os.environ.get("OPENAI_API_KEY"):
        # Lazy import langchain to avoid top-level import errors when AI is not used
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.schema import HumanMessage, SystemMessage
        except Exception as e:
            print("LangChain import failed, falling back to rule-based classifier:", e)
            return await _fallback_classify(item)

        chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        system = SystemMessage(content=(
            "You are an expense report policy assistant. Categorise single expense line items into one of: Travel, Meals, OfficeSupplies, Software, Hardware, Entertainment, Other. "
            "If the item likely violates company policy (e.g., excessive amount, personal expense), set policy_violation to true and provide a short reason."
        ))
        user_prompt = (
            f"Item: merchant={item.merchant}, amount={item.amount}, description={item.description}\n"
            "Respond ONLY with JSON: {\"category\": str, \"policy_violation\": bool, \"violation_reason\": str or null}\n"
        )
        # LangChain ChatOpenAI may be blocking; use to_thread
        try:
            response = await asyncio.to_thread(lambda: chat([system, HumanMessage(content=user_prompt)]))
            text = response.content.strip()
            import json
            data = json.loads(text)
            category = data.get("category")
            violation = bool(data.get("policy_violation"))
            reason = data.get("violation_reason")
        except Exception:
            # Parsing or call failed — fallback
            return await _fallback_classify(item)
    else:
        return await _fallback_classify(item)

    # Update session memory to keep decisions consistent for this merchant
    memory.set(item.merchant, category)
    return {"category": category, "policy_violation": violation, "violation_reason": reason}


async def _fallback_classify(item: Item) -> Dict[str, Any]:
    desc = (item.description or "").lower()
    merchant = item.merchant.lower()
    if "taxi" in merchant or "uber" in merchant or "lyft" in merchant:
        category = "Travel"
    elif any(k in desc for k in ["lunch", "dinner", "restaurant", "cafe", "coffee"]):
        category = "Meals"
    elif any(k in merchant for k in ["office", "supplies", "staples"]):
        category = "OfficeSupplies"
    elif any(k in desc for k in ["laptop", "phone", "monitor"]):
        category = "Hardware"
    elif item.amount and item.amount > 1000:
        category = "Hardware"
    else:
        category = "Other"
    violation = item.amount is not None and item.amount > 500
    reason = "Amount exceeds $500 threshold" if violation else None
    return {"category": category, "policy_violation": violation, "violation_reason": reason}


async def process_submitted_reports(use_ai: bool = True):
    memory = SessionMemory()
    # Find submitted reports
    cursor = Report.find(Report.status == "submitted")
    processed = 0
    async for report in cursor:
        changed = False
        print(f"Processing report {report.report_id} with {len(report.items)} items")
        for idx, it in enumerate(report.items):
            result = await classify_item(it, memory, use_ai=use_ai)
            if it.category != result["category"] or it.policy_violation != result["policy_violation"] or it.violation_reason != result["violation_reason"]:
                report.items[idx].category = result["category"]
                report.items[idx].policy_violation = result["policy_violation"]
                report.items[idx].violation_reason = result["violation_reason"]
                changed = True
                print(f" - Item {it.item_id}: set category={result['category']} violation={result['policy_violation']}")
        if changed:
            report.status = "processed"
            report.updated_at = __import__('datetime').datetime.utcnow()
            await report.save()
            processed += 1
    print(f"Processing complete, reports updated: {processed}")
    return processed
