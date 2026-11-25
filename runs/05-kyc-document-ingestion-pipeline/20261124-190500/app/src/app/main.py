import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from .db import init_db
from .openai_client import extract_entities
from .schemas import ExtractionSchema
from .models import Customer, ExtractedEntities
import asyncio

app = FastAPI(title="KYC Document Ingestion Sample")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except Exception:
        # For simplicity, only handle text uploads in this sample
        raise HTTPException(status_code=400, detail="Only text file uploads are supported in this sample. Please upload .txt files.")
    # Call OpenAI to extract fields
    try:
        extracted = await extract_entities(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    schema = ExtractionSchema(**extracted)
    # Map to Customer document
    cust = Customer(
        name=schema.name,
        dob=schema.dob,
        address=schema.address,
        government_id=schema.government_id,
        extracted=ExtractedEntities(name=schema.name, dob=schema.dob, address=schema.address, government_id=schema.government_id, raw=schema.raw)
    )
    cust.set_complete_if_valid()
    # Upsert
    await cust.upsert()
    return JSONResponse({"status": cust.status, "government_id": cust.government_id})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
