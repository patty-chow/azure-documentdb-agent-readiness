Dynamic Pricing Engine Sample (Azure DocumentDB + LangChain)

This sample demonstrates a Python LangChain agent that queries Azure DocumentDB (MongoDB-compatible) for demand metrics, competitor prices, and margin rules, then reasons step-by-step and writes an updated price atomically back to the product document.

What this sample shows
- How to connect to an Azure DocumentDB cluster using pymongo (singleton MongoClient).
- How to implement small data-access tools that query DocumentDB collections.
- How to wire those tools into a LangChain agent so the LLM can call them.
- How to perform an atomic find_one_and_update to record the recommended price.

Prerequisites
- Python 3.10+ (sample developed for 3.11)
- An Azure DocumentDB cluster reachable via the environment variable DOCUMENTDB_URI (mongodb+srv://... or mongodb://...)
- An OpenAI API key (if you want to run the LangChain agent): set OPENAI_API_KEY and optionally MODEL (default: gpt-4). You may adapt the code to Azure OpenAI or another provider.

Security note
Never commit secrets. The sample reads the connection string and model credentials from environment variables.

Files
- README.md (this file)
- requirements.txt
- .env.example
- db.py — MongoClient singleton and helper to create indexes
- seed.py — idempotent seed script that creates collections, indexes, and sample documents
- agent.py — LangChain tool wrappers around DocumentDB queries and the update tool
- main.py — CLI that runs the LangChain agent for a given SKU

Quickstart (local developer machine)
1) Create and activate a virtualenv (recommended)
   python -m venv .venv
   source .venv/bin/activate  # Unix/macOS
   .\.venv\Scripts\activate  # Windows

2) Install dependencies
   pip install -r requirements.txt

3) Configure environment (example .env shown in .env.example)
   export DOCUMENTDB_URI="<your-connection-string>"
   export OPENAI_API_KEY="<your-openai-key>"  # optional if you don't run the agent
   export MODEL="gpt-4"  # optional

4) Seed sample data (idempotent)
   python seed.py

5) Run the agent for a SKU (the agent will call DB tools and attempt to write the recommended price)
   python main.py SKU-001

6) Cleanup
   Remove the collections created, or use the Azure Portal if desired.

Notes and limitations
- This sample intentionally keeps the LLM prompt and tool behavior simple and deterministic for learnability.
- The sample does not provision Azure resources — it uses the existing cluster referenced by DOCUMENTDB_URI.
- The sample uses an atomic find_one_and_update but does not implement optimistic concurrency control.

License: MIT
