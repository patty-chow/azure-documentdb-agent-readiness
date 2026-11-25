from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

from app.config import settings
from app.models import Supplier, PurchaseOrder

app = FastAPI(title="Supplier & PO Management Sample")

client: AsyncIOMotorClient | None = None


@app.on_event("startup")
async def startup():
    global client
    client = AsyncIOMotorClient(settings.DOCUMENTDB_URI)
    db = client[settings.DATABASE_NAME]
    # Initialize Beanie with our document models
    await init_beanie(database=db, document_models=[Supplier, PurchaseOrder])


@app.on_event("shutdown")
async def shutdown():
    global client
    if client:
        client.close()


# Supplier CRUD
@app.post("/suppliers", response_model=dict)
async def create_supplier(supplier: Supplier):
    created = await supplier.insert()
    return created.dict()


@app.get("/suppliers", response_model=List[dict])
async def list_suppliers():
    docs = await Supplier.find_all().to_list()
    return [d.dict() for d in docs]


@app.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str):
    doc = await Supplier.get(supplier_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return doc.dict()


@app.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    doc = await Supplier.get(supplier_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Supplier not found")
    await doc.delete()
    return JSONResponse({"deleted": str(supplier_id)})


# Purchase Order CRUD
@app.post("/purchaseorders", response_model=dict)
async def create_purchase_order(po: PurchaseOrder):
    # Referential check: ensure supplier exists
    supplier = await Supplier.get(po.supplier_id)
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier does not exist")
    created = await po.insert()
    return created.dict()


@app.get("/purchaseorders", response_model=List[dict])
async def list_purchase_orders():
    docs = await PurchaseOrder.find_all().to_list()
    return [d.dict() for d in docs]


@app.get("/purchaseorders/{po_id}")
async def get_purchase_order(po_id: str):
    doc = await PurchaseOrder.get(po_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    return doc.dict()


@app.delete("/purchaseorders/{po_id}")
async def delete_purchase_order(po_id: str):
    doc = await PurchaseOrder.get(po_id)
    if not doc:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    await doc.delete()
    return JSONResponse({"deleted": str(po_id)})


# Aggregation: open PO value by supplier
@app.get("/aggregations/open_po_value_by_supplier")
async def open_po_value_by_supplier():
    if not client:
        raise HTTPException(status_code=500, detail="Database client not initialized")
    db = client[settings.DATABASE_NAME]
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
    results = []
    async for doc in cursor:
        # Convert ObjectId to str for JSON
        doc["supplier_id"] = str(doc.get("supplier_id"))
        results.append(doc)
    return results
