# Anti-Money-Laundering Pattern Detector (DocumentDB sample)

This is a small Python sample that demonstrates how to build a DocumentDB (MongoDB-compatible) aggregation-based AML detector and a tiny LangChain-capable agent that can summarize suspicious chains.

What this sample shows

- Connects to an existing Azure DocumentDB cluster via the DOCUMENTDB_URI environment variable.
- Creates a small sample dataset in the `sample_banking_01` database (`accounts` and `transactions` collections).
- Builds indexes used by the detector.
- Runs aggregation (attempts to use $graphLookup; falls back to client-side traversal if unsupported) to follow transaction references and assemble counterparty chains.
- Applies simple AML typology checks (structuring, rapid pass-through, circular transfers) and emits structured JSON narratives for flagged chains.
- Optionally uses OpenAI to generate polished narratives if OPENAI_API_KEY is provided; otherwise uses a built-in template.

Prerequisites

- Python 3.11+ (the environment this sample was built with provides Python 3.13).
- Network access to the DocumentDB cluster. The connection string must be set in DOCUMENTDB_URI.
- (Optional) OPENAI_API_KEY for LLM summaries.

Security

Do not commit secrets. The sample reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment. A .env.example is provided.

Quickstart

1. Create and activate a virtual environment (optional but recommended):

   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .\.venv\Scripts\activate  # Windows (PowerShell)

2. Install dependencies:

   pip install -r requirements.txt

3. Copy .env.example to .env and update:

   cp .env.example .env
   # fill DOCUMENTDB_URI, optionally OPENAI_API_KEY

4. Seed the sample data (idempotent):

   python src/seed_data.py

5. Run the detector (examines the seeded data and prints JSON narratives):

   python src/run_detector.py --limit 10

Files of interest

- src/db.py: Database connection helpers, runtime feature checks.
- src/seed_data.py: Idempotent seeding of accounts and transactions and index creation.
- src/detector.py: Aggregation tool and AML rule application, optional OpenAI summarization.
- src/run_detector.py: CLI to run the detector and print results.

Notes on verification

This sample was written to connect to a live DocumentDB cluster (DOCUMENTDB_URI). The build system may not run full end-to-end verification if DOCUMENTDB_URI is not present in the environment at build-time. See the Build Report for what was actually executed.
