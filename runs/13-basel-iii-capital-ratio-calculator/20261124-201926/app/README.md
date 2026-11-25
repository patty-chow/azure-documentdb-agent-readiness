Azure DocumentDB Basel III Capital Ratio Calculator

This sample shows how to build a small Python LangChain agent that exposes a DocumentDB aggregation tool to sum risk-weighted assets and capital elements across position documents and produce a board-ready Basel III capital adequacy commentary.

What this sample demonstrates
- Connect to a live Azure DocumentDB (MongoDB-wire) cluster using DOCUMENTDB_URI environment variable
- Create a sample `positions` collection and idempotently seed representative position documents
- Run a MongoDB aggregation that sums risk-weighted assets (rwa) and capital elements (capital.cet1, capital.total)
- Compute CET1 and Total Capital ratios and (optionally) run a LangChain agent that can interpret the results and write board-ready commentary comparing ratios to Basel III thresholds

Important: do not store secrets in files. Provide credentials via environment variables.

Prerequisites
- Python 3.10+ (a virtualenv is recommended)
- An Azure DocumentDB cluster reachable from this machine. Put the connection string in DOCUMENTDB_URI (already present in the run environment used for this sample).
- (Optional) To run the LangChain agent against OpenAI, set OPENAI_API_KEY in environment and install optional deps described below. If OPENAI_API_KEY is not set the sample will run in a deterministic fallback commentary mode.

Files
- main.py: sample CLI that runs the aggregation and produces commentary (LangChain agent used when OPENAI_API_KEY is provided)
- tools/aggregation_tool.py: small wrapper around pymongo that exposes an aggregation function
- seed_data.py: idempotent sample-data seeder that upserts a handful of position documents into sample_banking_13.positions
- requirements.txt: minimal requirements used for verification (pymongo, python-dotenv)
- .env.example: placeholders for DOCUMENTDB_URI and OPENAI_API_KEY

Quickstart
1. Create and activate a virtualenv, then install dependencies:

   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Set environment variables. Example (.env):

   DOCUMENTDB_URI="<your mongodb+srv://... connection string>"
   # Optional for LLM
   OPENAI_API_KEY="sk-..."

3. Seed sample data (idempotent):

   python seed_data.py

4. Run the sample to compute aggregates and produce board-ready commentary:

   python main.py

Notes on LangChain / LLM usage
- This repo intentionally keeps LangChain and OpenAI as optional runtime extras to allow verification of the DocumentDB aggregation without requiring LLM credentials. To enable the LangChain agent install these extras (example):

   pip install langchain openai

- When OPENAI_API_KEY is present, main.py will attempt to construct a LangChain agent with an aggregation tool. If the key is missing, main.py falls back to a deterministic, local commentary generator so the sample can still run without LLM keys.

Cleaning up
- The seed script writes to database `sample_banking_13` in a collection named `positions`. To remove the sample documents, use your preferred MongoDB client or the documentdb MCP server tools to delete the collection.
