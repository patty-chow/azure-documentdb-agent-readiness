Azure DocumentDB LangChain sample: inventory reorder multi-agent

What this sample shows
- A small Python LangChain multi-agent pattern: forecast agent, supplier agent, orchestrator.
- Forecast agent reads sales_velocity documents from Azure DocumentDB and computes reorder quantities.
- Supplier agent selects best supplier by lead time from lead_times collection.
- Orchestrator coordinates agents, writes purchase_order documents to DocumentDB, and uses a persisted agent_memory collection to avoid duplicate orders.

Prerequisites
- Python 3.x (this environment used Python 3.13)
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in .env or environment.
- (Optional) OpenAI API key in OPENAI_API_KEY for embedding/chat agents.

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env and fill DOCUMENTDB_URI and OPENAI_API_KEY
4. python seed.py   # creates collections, indexes, and inserts demo data
5. # Run orchestrator for demo (creates purchase orders)
   python run_orchestrator.py --all

Files
- seed.py: idempotent seed script (creates indexes and sample data)
- sample_retail_09/db.py: MongoClient singleton and helpers
- sample_retail_09/agents.py: forecast_agent, supplier_agent, and orchestrator implementation
- run_orchestrator.py: CLI to trigger orchestration for all or one SKU
- .env.example: placeholder for secrets
- requirements.txt

Security
- Do not commit secrets. Read DOCUMENTDB_URI and API keys from environment as shown.

Cleanup
- Manually drop the `sample_retail_09` database using your preferred client if desired.

Notes
- This sample targets demo and learning; it is not production-ready. Index shapes and timeouts are chosen for clarity.
