# 3. Build report: 19-proactive-outreach-orchestration

**Status: completed**

A small Node.js LangChain-style orchestration sample was created that monitors DocumentDB events (seeded), generates personalized outreach (LLM fallback or OpenAI if configured), records/send (sandbox) actions to outreach_logs, and exposes a small REST endpoint to inspect logs. The sample uses a singleton MongoClient, reads secrets from environment variables, and includes idempotent seeding and index creation. I verified seeding, index creation, processing of sample events (one-shot), and that outreach_logs were written to the live DocumentDB cluster via the provided documentdb MCP server tools.

## How to run

1) Copy .env.example to .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want real LLM calls).
2) npm install
3) npm run seed   # idempotent: creates customers, events and simple indexes
4) npm run run-once   # process qualifying events once (writes outreach_logs)
5) npm start   # starts long-running change-stream listener (optional)
6) npm run server   # starts REST server on PORT (GET /logs returns recent outreach logs)
7) npm test   # runs the simple smoke-runner (seed + run-once)

Notes: The sample defaults to SANDBOX_SEND=true to avoid sending real messages. To enable real sending, implement the provider logic in src/sendAgent.js and set SANDBOX_SEND=false (do not commit provider secrets).

## Verified by running

- npm install: exit code 0 (dependencies installed)
- seed script: node src/seed.js -> 'Seeding complete.' (customers, events created and indexes on events.customerId, events.type, outreach_logs.eventId created)
- documentdb_list_databases (MCP): database 'sample_customer_360_19' with collections customers (3), events (3), outreach_logs (0) observed
- documentdb_list_indexes (MCP) on 'events': _id_, customerId_1, type_1 observed
- documentdb_list_indexes (MCP) on 'outreach_logs': _id_, eventId_1 observed
- run-once: node src/run_once.js processed 3 qualifying events and created 3 outreach_logs documents (sandbox sends logged to console)
- documentdb_find_documents (MCP) on 'outreach_logs': 3 documents returned with expected fields (logId, eventId, customerId, channel, message, status, sentAt)
- npm test (smoke runner): ran seed and run-once successfully

## Not verified

- Long-running change-stream listener (npm start) was not started under test (avoids background long-running processes in CI). The code is present and ready to run manually.
- Express REST server (npm run server) was not exercised in verification; endpoint GET /logs is implemented but not started during automated verification.
- Real OpenAI API call behavior: code path attempts OpenAI when OPENAI_API_KEY is present. I did not run live LLM calls because OPENAI_API_KEY may not be set in this environment; safe fallback generates deterministic templated messages. The exact OpenAI SDK call shape used may require minor adjustments if OpenAI client changes; verify with your provider key.
- Vector index creation (cosmosSearch / vector indexes) and searches: the sample creates standard single-field indexes only. I did not create nor verify a DocumentDB vector index (cosmosSearchOptions) or any $search pipelines — the readiness report recommended a specialist createIndexes shape; I included guidance but did not programmatically create a vector index against the cluster.
- LangChain-specific orchestration: the sample demonstrates a LangChain-style pipeline (trigger -> copy agent -> send agent) but does not use the langchain npm constructs heavily. If you prefer a full LangChain Chain/LLMChain composition, that can be added; I avoided adding heavy LangChain-only code paths so the sample runs without an API key.
- Tests that call a real LLM or send provider: not executed (tests use the offline fallback).

## Open issues

- If you want integrated vector search (cosmosSearch + vector indexes) the repo should add an idempotent index-creation script that calls the DocumentDB createIndexes command with cosmosSearchOptions (vector-hnsw|ivf|diskann). The DocumentDB 'createIndexes' shape differs from the MongoDB createIndex helper and should follow Learn docs; I did not create that index because vector search selection and embedding model dimensions are environment/usage-dependent.
- The OpenAI chat API call in src/copyAgent.js uses an SDK call pattern that is commonly used but subject to provider SDK version changes. If you run with OPENAI_API_KEY set and see errors, adjust the OpenAI client usage per your installed openai package version.
- Send-agent is sandboxed by default. To send real messages, implement provider calls in src/sendAgent.js and add necessary env vars (SMTP, Twilio, etc.). Be careful not to commit production secrets.
- mongosh is not available in the environment (readiness report). For interactive manual checks, install mongosh locally or rely on the documentdb MCP server tools included here.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/seed.js`
- `src/copyAgent.js`
- `src/sendAgent.js`
- `src/orchestrator.js`
- `src/run_once.js`
- `src/listener.js`
- `src/server.js`
- `src/test_runner.js`

