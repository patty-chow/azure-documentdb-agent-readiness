# 3. Build report: 14-dynamic-pricing-engine

**Status: completed**

Built a Python sample demonstrating a LangChain-style agent pattern that uses DocumentDB (MongoDB-compatible) for a dynamic pricing engine. The repo contains an idempotent seed script, a DB client singleton with index initialization, tool wrappers that query DocumentDB (competitor prices, demand metrics, margin rules) and an atomic update tool to write a recommended price. I verified dependency installation, seeded the sample database, inspected collections/documents via the documentdb MCP server, and ran the sample CLI for SKU-001 — the deterministic fallback pricing logic executed and performed an atomic find_one_and_update to save the recommended price. The model-driven (OpenAI) path is present but was not executed because OPENAI_API_KEY was not set in this environment; the code falls back to deterministic logic in that case.

## How to run

1) Create/activate a Python 3.10+ virtualenv.
   python -m venv .venv
   source .venv/bin/activate  # Unix/macOS

2) Install dependencies
   pip install -r requirements.txt

3) Set environment variables (example in .env.example):
   export DOCUMENTDB_URI="mongodb+srv://<username>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true"
   # Optional: to run the LLM path
   export OPENAI_API_KEY="sk-..."
   export MODEL="gpt-4"

4) Seed sample data (idempotent)
   python seed.py

5) Run the sample CLI for a SKU (uses deterministic fallback if OPENAI_API_KEY not set):
   python main.py SKU-001

6) The script will print the recommendation and perform an atomic update to the products collection.


## Verified by running

- pip install -r requirements.txt: exit code 0 (dependencies installed or already present)
- seed.py: ran and completed successfully, created/updated indexes and inserted sample documents
- documentdb_list_databases (MCP): returned database list including sample_retail_14
- documentdb_sample_documents (MCP) for products, competitor_prices, demand_metrics, margin_rules: returned sample documents (observed seed docs present)
- python main.py SKU-001: ran deterministic fallback logic (no OPENAI_API_KEY) and performed atomic update on products (find_one_and_update) — update result returned and product document updated

## Not verified

- Model-driven LangChain agent path (calling OpenAI/Chat model) not executed because OPENAI_API_KEY was not set in the environment; code path is present but unverified.
- A full LangChain initialize_agent-based implementation was not executed or validated due to LangChain import/API differences in the environment; I used a lightweight orchestration approach instead and logged that decision with evidence.
- Vector search, hybrid retrieval or integrated DocumentDB cosmosSearch features were not used or verified in this sample (not required by the prompt).

## Open issues

- LangChain version / API differences: Attempting to import ChatOpenAI / langchain.llms failed in this environment. To run a LangChain initialize_agent-based agent, update the project to a LangChain version whose API supports ChatOpenAI or adjust imports to match your installed LangChain. I logged the decision to avoid brittle initialize_agent usage and implemented a lightweight orchestration as a stable, runnable fallback (see D024).
- If you want the sample to call a hosted LLM (OpenAI/Azure OpenAI) during runs, set OPENAI_API_KEY and MODEL before running main.py. The sample will then call the model and attempt to parse its JSON response — model outputs may vary, so further prompt-engineering or parsing robustness may be desired for production use.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `db.py`
- `seed.py`
- `agent.py`
- `main.py`

