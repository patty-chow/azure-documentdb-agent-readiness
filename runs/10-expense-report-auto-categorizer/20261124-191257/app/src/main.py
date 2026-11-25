import asyncio
from beanie import PydanticObjectId
from .db import init_db, close_db
from .models import Report, Decision
from .processor import categorize_item

class SimpleMemory:
    def __init__(self):
        self.buffer = []
    def add(self, role, text):
        self.buffer.append({"role": role, "text": text})
    def get_messages(self):
        return self.buffer

async def process_reports():
    await init_db([Report, Decision])
    memory = SimpleMemory()
    # Find submitted reports
    cursor = Report.find({"status": "submitted"})
    processed = 0
    async for rpt in cursor:
        print(f"Processing report {rpt.report_id}")
        updated = False
        for it in rpt.items:
            item_dict = it.dict()
            category, violation, reason = await categorize_item(item_dict, memory)
            if it.category != category or it.policy_violation != violation:
                it.category = category
                it.policy_violation = violation
                it.violation_reason = reason
                updated = True
        if updated:
            rpt.updated_at = __import__('datetime').datetime.utcnow()
            await rpt.save()
            print(f"Updated report {rpt.report_id}")
            processed += 1
        else:
            print(f"No changes for {rpt.report_id}")
    await close_db()
    print(f"Done. Reports updated: {processed}")

if __name__ == "__main__":
    asyncio.run(process_reports())
