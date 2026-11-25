Crypto Wallet Activity Analyzer (sample_fintech_09)

This sample demonstrates a Python LangChain-based agent that analyzes wallet transaction activity stored in an Azure DocumentDB (MongoDB-compatible) cluster. The agent uses a DocumentDB aggregation tool to compute daily transaction volume and frequency for a given wallet address, performs simple statistical outlier detection, and returns a plain-language summary.

What this sample shows
- How to connect to an Azure DocumentDB cluster with pymongo using a singleton MongoClient
- How to create a compound index { wallet_address: 1, timestamp: 1 } to support time-range aggregations
- How to seed a demo `transactions` collection with synthetic data (idempotent)
- A simple "DocumentDB aggregation tool" callable from Python that runs the aggregation pipeline server-side
- A LangChain-based flow (with optional OpenAI summarization) and an offline fallback summarizer so the sample runs without cloud LLM credentials

Prerequisites
- Python 3.10+ (the environment used to build this sample has Python on PATH)
- An Azure DocumentDB connection string in the environment variable DOCUMENTDB_URI. Example (do NOT put a real secret here):

  DOCUMENTDB_URI=mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com:10260/?ssl=true&authSource=admin

- Optional: OPENAI_API_KEY if you want the agent to use the OpenAI API for nicer natural-language summaries. If not set, the sample uses a local rule-based summarizer.

Files
- src/sample_fintech_09/: Python package with the app
- scripts/seed_data.py: idempotent seed script to create `transactions` collection and insert synthetic transactions
- .env.example: example env variables
- requirements.txt: Python dependencies

How to run
1. Create and activate a virtual environment (optional but recommended):
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .\.venv\Scripts\activate  # Windows

2. Install dependencies:
   pip install -r requirements.txt

3. Set DOCUMENTDB_URI in your shell (and OPENAI_API_KEY if you have one):
   export DOCUMENTDB_URI="<your connection string>"

4. Seed the demo data (writes to the database):
   python -m sample_fintech_09.seed --wallet WALLET1 --days 30 --tx-per-day 10

5. Run the analyzer for a wallet address:
   python -m sample_fintech_09 analyze WALLET1

Cleanup
- The seed script inserts documents into the `sample_fintech_09` database in a `transactions` collection. To clean up, delete the collection using your preferred MongoDB tool or the Azure portal.

Security
- This sample reads the DocumentDB connection string from the DOCUMENTDB_URI environment variable and never writes secrets to disk.

Notes
- The sample will create an index on { wallet_address: 1, timestamp: 1 } if it does not exist; the sample also calls the documentdb MCP server's explain tool (if available) to verify index usage during verification steps.
