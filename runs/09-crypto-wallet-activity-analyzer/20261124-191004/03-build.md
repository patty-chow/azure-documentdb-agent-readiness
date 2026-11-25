# 3. Build report: 09-crypto-wallet-activity-analyzer

**Status: completed**

Created a small Python sample app (sample_fintech_09) that connects to an existing Azure DocumentDB cluster (read from DOCUMENTDB_URI), seeds a demo `transactions` collection with idempotent synthetic data, creates a compound index { wallet_address: 1, timestamp: 1 }, runs a server-side aggregation that groups transactions by day (daily total and count), performs simple z-score outlier detection, and returns a plain-language summary. The sample supports optional OpenAI summarization (OPENAI_API_KEY) and falls back to a local rule-based summarizer so it runs with no cloud LLM credentials. I verified dependency installation, seeding, index creation, explain-plan index usage, and the analyzer run against the live cluster.

## How to run

1) Create & activate a venv (optional): python -m venv .venv && source .venv/bin/activate
2) Install deps: pip install -r requirements.txt
3) Set DOCUMENTDB_URI in your environment (and optional OPENAI_API_KEY). Do not commit secrets.
4) Seed data (idempotent): python scripts/run_seed.py --wallet <WALLET> --days 30 --tx-per-day 5
5) Analyze a wallet: python scripts/run_analyze.py <WALLET>
Notes: The sample reads DOCUMENTDB_URI at runtime. If OPENAI_API_KEY is present the sample will attempt an OpenAI ChatCompletion call; otherwise the local summarizer is used.

## Verified by running

- pip install -r requirements.txt: success (dependencies installed)
- Seed script run (python scripts/run_seed.py --wallet TEST_WALLET_1 --days 10 --tx-per-day 3): success — seeded 30 transactions for wallet TEST_WALLET_1 into sample_fintech_09.transactions
- documentdb_explain_operation (aggregate) against sample_fintech_09.transactions for wallet TEST_WALLET_1: success — explain output returned and shows the compound index idx_wallet_time being used by an IXSCAN
- documentdb_list_indexes for sample_fintech_09.transactions: success — indexes include _id_ and idx_wallet_time (compound on wallet_address and timestamp)
- Analyzer run (python scripts/run_analyze.py TEST_WALLET_1): success — produced a plain-language summary (local summarizer path used)

## Not verified

- OpenAI summarization path (calls to OpenAI API) was not executed because OPENAI_API_KEY was not provided in the environment; therefore LLM-based summary behavior and prompts were not validated against a live model.
- LangChain agent orchestration: the sample demonstrates a LangChain-friendly design and optional LLM integration, but a full LangChain Agent (initialize_agent flow) was not exercised; instead a small tool + optional OpenAI path and a local summarizer were implemented to keep the sample runnable without external LLM credentials.

## Open issues

None.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `src/sample_fintech_09/__init__.py`
- `src/sample_fintech_09/db.py`
- `src/sample_fintech_09/tools.py`
- `src/sample_fintech_09/seed.py`
- `src/sample_fintech_09/analyze.py`
- `src/sample_fintech_09/__main__.py`
- `scripts/run_seed.py`
- `scripts/run_analyze.py`

