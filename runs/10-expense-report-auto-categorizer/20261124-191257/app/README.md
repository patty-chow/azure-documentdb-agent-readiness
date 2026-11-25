Expense Report Auto-Categorizer (Azure DocumentDB + Beanie + LangChain)

What this sample shows
- A small Python async sample using Beanie ODM to model expense reports in Azure DocumentDB.
- A LangChain-driven categoriser that labels line items against company policy, flags violations, and persists enriched reports back to the database.
- In-session agent memory to apply consistent categorisation decisions across multiple reports.

Prerequisites
- Python 3.10+ (3.11 recommended)
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in .env from the cluster connection string (SRV form is recommended).
- (Optional) OPENAI_API_KEY to enable the real AI-driven categoriser. If absent, the sample uses a deterministic fallback for demos.

Quick start
1. Create and activate a virtualenv:
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you have one).
4. Seed sample data:
   python -m src.seed
5. Run the demo processing run in deterministic (no-AI) mode:
   python main.py --no-ai

To run with real AI (LangChain + OpenAI):
- Set OPENAI_API_KEY in .env (and ensure USE_AI=true). Then run:
  python main.py

Files
- src/models.py — Beanie Document models for Report and Item
- src/db.py — DB initialization and Motor client
- src/seed.py — idempotent sample-data seeder
- src/processor.py — agent-driven processing pipeline (uses LangChain when OPENAI_API_KEY present)
- main.py — CLI entrypoint

Notes and choices
- Driver: Motor is used to integrate with Beanie (decision logged). The documentdb-connection skill recommends PyMongo's AsyncMongoClient for new code, but Beanie currently integrates with Motor.
- No vector indexes or embeddings were created. The sample focuses on classification via the LLM.

Cleanup
- Delete the sample documents from the collection using your preferred MongoDB tool or the MCP server.

License: MIT
