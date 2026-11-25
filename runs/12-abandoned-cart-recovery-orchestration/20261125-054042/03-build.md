# 3. Build report: 12-abandoned-cart-recovery-orchestration

**Status: completed**

Built a small Node.js LangChain sample that implements an abandoned-cart recovery orchestration against an existing Azure DocumentDB (MongoDB-compatible) cluster. The sample includes an idempotent seed script, a pipeline (find carts >2 hours old → generate personalised copy via LangChain/OpenAI → simulate channel send (email/SMS) → log outcome back to DocumentDB), unit tests (Jest), and documentation. I verified the app by installing dependencies, running tests, seeding the live cluster, running the pipeline once, and inspecting the created indexes and logs via the documentdb MCP tools.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI (required) and optionally OPENAI_API_KEY. 2) npm install 3) npm run seed  # idempotent seed 4) npm start       # runs pipeline once (simulated sends) 5) npm test        # runs unit test (mocks)  Note: pipeline is a one-shot CLI (node src/run.js). For production scheduling, run it periodically (cron/Functions/Logic Apps) and add idempotency/metrics as needed.

## Verified by running

- npm install: 0 exit (dependencies installed).
- npm test (Jest): passed (1 test) — tests/run.test.js passed (mocked pipeline).
- npm run seed: exit 0 — seed script inserted idempotent sample customers and carts into sample_retail_12 database.
- npm start: exit 0 — pipeline executed once; found abandoned carts, generated simulated messages, simulated sends and logged outcomes.
- documentdb_list_indexes (carts): index lastUpdated found (name: lastUpdated_1).
- documentdb_list_indexes (recovery_logs): index cartId found (name: cartId_1).
- documentdb_find_documents (recovery_logs): 2 log documents returned for the two simulated sends.

## Not verified

- Real OpenAI LLM calls: Not verified with a real OPENAI_API_KEY in this run. The copy-agent falls back to a simulated response when OpenAI is not configured. Reason: OPENAI_API_KEY was not provided in the environment for this build.
- Real message delivery via Twilio/SendGrid: Not executed. The channel agent is currently implemented to simulate sends and prints activity to stdout. The sample includes .env.example placeholders and notes on how to wire real providers.
- Vector and full-text index creation: The sample demonstrates basic indexes required for the query (lastUpdated, cartId). It does not create vector or search indexes because the sample's flow does not require semantic or vector search. If you want to demonstrate documentdb vector/search features, additional code and indexes would be added and verified.
- Provisioning Azure resources: Not performed. The run policy forbids Azure writes and the environment already provides an accessible DocumentDB cluster; seed and pipeline used that cluster.

## Open issues

- If you want live LLM outputs, set OPENAI_API_KEY in .env (or environment) before running the pipeline; the sample currently uses a simulated fallback if Key or LangChain/OpenAI combination cannot be instantiated during runtime.
- To send real messages, implement Twilio/SendGrid SDK usage in src/agents/channelAgent.js and populate the corresponding env vars (TWILIO_*/SENDGRID_API_KEY). For safety, sends are simulated in the shipped sample.
- The sample is intentionally small; production-ready extensions (retries, idempotency markers/unique log keys to avoid double-sends, more robust error handling, metrics) should be added before use in production.

## Files

- `package.json`
- `package-lock.json`
- `jest.config.cjs`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/seed.js`
- `src/run.js`
- `src/agents/copyAgent.js`
- `src/agents/channelAgent.js`
- `tests/run.test.js`

