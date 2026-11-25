Supplier & Purchase Order management sample (FastAPI + Beanie)

This sample demonstrates:
- A Python FastAPI service using Beanie ODM against Azure DocumentDB (MongoDB-compatible)
- Supplier and PurchaseOrder documents with Pydantic validation
- Full CRUD endpoints for both entities
- An aggregation endpoint that summarizes open PO value by supplier

Prerequisites
- Python 3.8+ (the build used Python 3.13)
- A reachable Azure DocumentDB cluster connection string in the environment variable DOCUMENTDB_URI

Setup
1. Copy .env.example to .env and set DOCUMENTDB_URI
2. Create a virtual environment and install dependencies:
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

Run the seed script (idempotent):
   python -m app.seed

Run the app locally (development):
   uvicorn app.main:app --reload

Notes
- The app uses the database named sample_retail_15 and will not touch other databases.
- Do not commit credentials. Use .env and environment variables.
- For production, consider using Decimal for money values and stronger validation.
