import asyncio
import os
import uuid
from datetime import datetime
from .db import init_db
from .models import Report, Item

SAMPLE_REPORTS = [
    {
        "report_id": "REP-001",
        "submitter": "alice@example.com",
        "items": [
            {"item_id": "1", "date": "2026-01-02T00:00:00", "merchant": "CoffeeCo", "amount": 4.5, "description": "latte"},
            {"item_id": "2", "date": "2026-01-03T00:00:00", "merchant": "TaxiNow", "amount": 45.0, "description": "airport ride"},
        ],
    },
    {
        "report_id": "REP-002",
        "submitter": "bob@example.com",
        "items": [
            {"item_id": "1", "date": "2026-02-10T00:00:00", "merchant": "FancyRestaurant", "amount": 400.0, "description": "client dinner"},
            {"item_id": "2", "date": "2026-02-11T00:00:00", "merchant": "Office Supplies", "amount": 23.0, "description": "notebook"},
        ],
    },
    {
        "report_id": "REP-003",
        "submitter": "carol@example.com",
        "items": [
            {"item_id": "1", "date": "2026-03-01T00:00:00", "merchant": "GadgetStore", "amount": 1200.0, "description": "new laptop"},
            {"item_id": "2", "date": "2026-03-02T00:00:00", "merchant": "TaxiNow", "amount": 30.0, "description": "ride"},
        ],
    },
]

async def seed():
    await init_db()
    created = 0
    for r in SAMPLE_REPORTS:
        # Idempotent upsert by report_id
        existing = await Report.find_one(Report.report_id == r["report_id"])
        items = []
        for it in r["items"]:
            item = Item(
                item_id=it["item_id"],
                date=datetime.fromisoformat(it["date"]),
                merchant=it["merchant"],
                amount=it["amount"],
                description=it.get("description"),
            )
            items.append(item)
        if existing:
            existing.items = items
            existing.submitter = r.get("submitter")
            existing.status = "submitted"
            existing.updated_at = datetime.utcnow()
            await existing.save()
        else:
            doc = Report(report_id=r["report_id"], submitter=r.get("submitter"), items=items)
            await doc.insert()
            created += 1
    print(f"Seed complete, created={created}")

if __name__ == "__main__":
    asyncio.run(seed())
