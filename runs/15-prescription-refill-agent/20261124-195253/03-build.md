# 3. Build report: 15-prescription-refill-agent

**Status: completed**

Built a small Node.js sample app that demonstrates using Azure DocumentDB (MongoDB wire) to look up prescriptions, check refill eligibility, create refill requests, and persist simple agent memory so follow-up requests (e.g. "refill my blood pressure medication") resolve to the previously referenced medication. I resolved the prompt contradiction (Beanie is Python-only vs Node.js) by implementing the sample in Node.js with Mongoose and a lightweight rule-based agent (pluggable to an LLM). The repo includes an idempotent seed script that creates sample data and indexes in the required database (sample_healthcare_15). I verified the seed, exercised the agent logic against the live cluster, created a refill request, and validated the created documents and index presence using the documentdb MCP server tools.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster's MongoDB connection string (do not commit secrets). 2) npm install. 3) npm run seed — this creates indexes and sample documents in database 'sample_healthcare_15'. 4) (optional) npm start to run the Express server and call POST /chat with JSON {patientId, message}. 5) Examples: curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{"patientId":"patient-1","message":"Please refill my lisinopril"}'. The agent is implemented as a small, rule-based component and is pluggable to an LLM via OPENAI_API_KEY; see README for details.

## Verified by running

- npm install: succeeded (packages installed)
- npm run seed: succeeded (seed script inserted sample prescriptions and created indexes)
- documentdb_list_databases sample_healthcare_15: returned collections prescriptions (3) and refillrequests (0) after seed
- documentdb_find_documents prescriptions: returned the 3 seeded prescriptions
- Agent process run (patient-1, 'Please refill my lisinopril'): returned 'Refill requested...' and created a refillRequests document
- documentdb_find_documents refillrequests: confirmed the refill request document was inserted
- documentdb_find_documents prescriptions (rx-1001): confirmed refillCount was decremented after refill request
- Agent follow-up run (patient-1, 'refill my blood pressure medication'): memory resolved to Lisinopril and returned an eligibility response

## Not verified

- LangChain / OpenAI integration: not exercised (no external LLM calls were made). Code is pluggable to enable OpenAI by setting OPENAI_API_KEY, but I did not verify live LLM calls or embedding-based fuzzy medication matching because no API key was provided and to keep verification self-contained.
- End-to-end Express server HTTP flows via external HTTP client: I tested agent logic via direct Node invocations; I did not run a long-running server process under the command runner beyond the direct Node calls.
- Any provisioning of a DocumentDB cluster: intentionally not attempted because run policy forbids Azure resource writes. I used the pre-provisioned cluster reachable in DOCUMENTDB_URI as required by the prompt.

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/models/Prescription.js`
- `src/models/RefillRequest.js`
- `src/models/AgentMemory.js`
- `src/agent.js`
- `src/index.js`
- `scripts/seed.js`

