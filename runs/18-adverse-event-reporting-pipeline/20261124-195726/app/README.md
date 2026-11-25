Adverse Event Reporting sample for Azure DocumentDB (MongoDB wire protocol) using Beanie ODM and FastAPI.

This sample shows:
- Accepting free-text adverse-event reports via POST /reports, using an LLM to extract structured fields (drug, event, severity, onset_date), validating with Pydantic/Beanie, and storing into Azure DocumentDB.
- A simple aggregation endpoint GET /reports/top-events that returns most frequently reported events by drug.

Prerequisites
- Python 3.10+ (this run used system Python 3.13)
- An Azure DocumentDB cluster reachable from this machine. Set the connection string in DOCUMENTDB_URI.
- (Optional) OpenAI API key in OPENAI_API_KEY to enable LLM-based extraction. Without it, seed.py loads synthetic structured documents directly.

Quickstart
1. Create and activate a virtualenv, then install:
   python -m pip install -r requirements.txt
2. Set environment variables (or copy .env.example to .env and edit):
   export DOCUMENTDB_URI="your-uri"
   export DOCUMENTDB_DATABASE=sample_healthcare_18
   export OPENAI_API_KEY="sk-..."  # optional
3. Seed sample data (if OPENAI_API_KEY is unset, pre-parsed examples are inserted):
   python seed.py
4. Run the API:
   uvicorn src.main:app --reload
5. POST free-text to http://127.0.0.1:8000/reports with JSON {"text": "..."}
6. GET aggregations at http://127.0.0.1:8000/reports/top-events

Testing
- pytest will run lightweight unit tests (some integration tests require DOCUMENTDB_URI).

Design notes
- Beanie 2.2.0 + PyMongo 4.19.0 used per Azure quickstart.
- Index: compound index on {drug, event} created at startup to speed aggregation.
- No secrets are written to the repo; read from env at runtime.

Cleanup
- To remove sample data, connect to the database and drop the 'adverse_events' collection or the entire 'sample_healthcare_18' database.
