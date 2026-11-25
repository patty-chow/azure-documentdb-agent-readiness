Azure DocumentDB CLV Prediction Sample

This sample shows how to build a simple Python LangChain agent that uses a DocumentDB aggregation tool
to compute customer metrics (purchase frequency, average order value, tenure) and then asks an LLM to
assign a CLV score and tier (low/medium/high/VIP) with a rationale. The computed score, tier and rationale
are written back to the customer document in the `sample_customer_360_12` database, `customers` collection.

Prerequisites
- Python 3.10+ (this environment uses Python 3.13)
- A reachable Azure DocumentDB cluster. Set the DOCUMENTDB_URI environment variable to the MongoDB URI.
- OpenAI credentials (OPENAI_API_KEY) if you want to run the LangChain agent portion.

Files
- run_clv.py             # CLI entrypoint: seed sample data and run CLV for a customer
- src/db.py              # MongoClient singleton and helpers
- src/seed.py            # Idempotent seed script creating sample customers
- src/clv_tool.py        # Aggregation functions to compute metrics and update profiles
- src/agent.py           # LangChain agent wiring and prompt engineering
- .env.example           # Example environment variables
- requirements.txt       # Python dependencies

How to run
1) Create a virtualenv and install dependencies
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2) Set environment variables (or use a .env file)
   export DOCUMENTDB_URI="<your-docdb-uri>"
   export OPENAI_API_KEY="<your-openai-key>"

3) Seed sample data and run the CLV agent for a sample customer
   python run_clv.py --seed --customer-id sample_cust_1

4) To run tests (they will use the DOCUMENTDB_URI env var):
   pytest -q

Security and cleanup
- This sample reads sensitive keys from environment variables. Do not check secrets into source control.
- To remove sample documents, run `python src/seed.py --cleanup` (implemented as a convenience).
