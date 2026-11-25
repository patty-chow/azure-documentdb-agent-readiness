import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models import Supplier, PurchaseOrder
from datetime import datetime


async def seed():
    client = AsyncIOMotorClient(settings.DOCUMENTDB_URI)
    db = client[settings.DATABASE_NAME]
    await init_beanie(database=db, document_models=[Supplier, PurchaseOrder])

    # Idempotent seed: create suppliers if none
    existing = await Supplier.find_all().to_list()
    if not existing:
        s1 = Supplier(name="Acme Corp", contact={"email": "procure@acme.example.com"})
        s2 = Supplier(name="Contoso Ltd", contact={"email": "po@contoso.example.com"})
        await s1.insert()
        await s2.insert()
        print("Inserted sample suppliers")
    else:
        print("Suppliers already present, skipping insert")

    # Create a couple of purchase orders
    pos = await PurchaseOrder.find_all().to_list()
    if not pos:
        suppliers = await Supplier.find_all().to_list()
        if not suppliers:
            print("No suppliers found after insert — aborting")
            return
        s0 = suppliers[0]
        s1 = suppliers[1] if len(suppliers) > 1 else suppliers[0]
        await PurchaseOrder(supplier_id=s0.id, total_value=1200.0, status="open").insert()
        await PurchaseOrder(supplier_id=s0.id, total_value=300.0, status="closed").insert()
        await PurchaseOrder(supplier_id=s1.id, total_value=450.0, status="open").insert()
        print("Inserted sample purchase orders")
    else:
        print("Purchase orders already present, skipping insert")

    # Run the aggregation and print results
    pipeline = [
        {"$match": {"status": "open"}},
        {"$group": {"_id": "$supplier_id", "open_value": {"$sum": "$total_value"}}},
        {"$lookup": {
            "from": "suppliers",
            "localField": "_id",
            "foreignField": "_id",
            "as": "supplier"
        }},
        {"$unwind": {"path": "$supplier", "preserveNullAndEmptyArrays": True}},
        {"$project": {"supplier_id": "$_id", "supplier_name": "$supplier.name", "open_value": 1, "_id": 0}}
    ]
    cursor = db[PurchaseOrder.get_motor_collection().name].aggregate(pipeline)
    print("Open PO value by supplier:")
    async for doc in cursor:
        print({"supplier_id": str(doc.get("supplier_id")), "supplier_name": doc.get("supplier_name"), "open_value": doc.get("open_value")})

    await client.close()


if __name__ == "__main__":
    asyncio.run(seed())
