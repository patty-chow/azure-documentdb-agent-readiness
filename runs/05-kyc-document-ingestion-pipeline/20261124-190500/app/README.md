KYC Document Ingestion Sample

Overview

This sample demonstrates an async Python ingestion pipeline using FastAPI and Beanie ODM to accept KYC documents, call OpenAI for structured extraction (name, dob, address, government_id), validate the extracted JSON with Pydantic, and upsert the customer record into Azure DocumentDB (MongoDB-compatible). Incomplete records are flagged for manual review.

Prerequisites

- Python (3.11+; sample developed on Python 3.13)
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in environment
- OPENAI_API_KEY for OpenAI calls

Setup

1. Create a virtualenv and install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY.

3. Start the API:

   uvicorn src.app.main:app --reload

4. Use scripts/seed.py to upload three sample documents (app must be running):

   python scripts/seed.py

Notes

- The sample uses Beanie + Motor for async MongoDB access. For production, follow the documentdb-connection skill guidance about connection pooling and singleton clients.
- Only simple text file uploads (.txt) are handled by the sample. For real KYC PDFs, add OCR extraction before calling OpenAI.
- The sample reads secrets from environment variables; do not commit real secrets.

Cleanup

- Delete the "customers" collection from the sample_fintech_05 database using your preferred MongoDB tool or the documentdb MCP server.

Files

- src/app: application code
- scripts/seed.py: client to upload sample docs
- .env.example: environment variable placeholders
