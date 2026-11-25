Azure DocumentDB - Order History Timeline Agent (sample)

This sample demonstrates a Python LangChain-based conversational agent that connects to an Azure DocumentDB (MongoDB-compatible) cluster to fetch order history, run spend-aggregation pipelines, and look up order status. It keeps conversational memory so follow-ups like "what about last month?" resolve against the previously-mentioned customer/time range.

Prerequisites
- Python 3.10+ installed (this workspace uses the system python).
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in a .env file or your environment (never commit secrets).
- (Optional but required to run the LLM-backed agent) OPENAI_API_KEY in environment.

What the sample includes
- seed.py: idempotent seeder that inserts sample orders into database `sample_retail_06` collection `orders`.
- src/agent/db.py: MongoDB client, index creation, query and aggregation helpers.
- src/agent/agent.py: a small LangChain agent wrapper with tools for order-history, spend summary, and order lookup. If OPENAI_API_KEY is missing, run_agent.py falls back to a deterministic scripted flow so the sample can be demonstrated without an LLM.
- run_agent.py: example interactive/scripted demonstration (first query + follow-up "what about last month?").
- tests/: simple integration tests that run against the live cluster.
- .env.example: placeholder for DOCUMENTDB_URI and OPENAI_API_KEY

Quick start
1. Create and activate a virtualenv (recommended):
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Copy .env.example to .env and fill DOCUMENTDB_URI and OPENAI_API_KEY (if you want LLM features):
   cp .env.example .env

4. Seed sample data (idempotent):
   python seed.py

5. Run the agent demonstration (interactive or scripted):
   python run_agent.py

6. Run tests (they use the live cluster):
   pytest -q

Notes
- The code reads DOCUMENTDB_URI at runtime from the environment. Do not commit real credentials.
- The sample creates indexes and upserts documents into database `sample_retail_06` only.
- This sample does not provision or modify Azure resources (no control-plane changes). It uses the existing cluster provided by the environment.

License: MIT
