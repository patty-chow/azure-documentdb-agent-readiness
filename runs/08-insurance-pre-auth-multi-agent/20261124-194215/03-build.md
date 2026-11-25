# 3. Build report: 08-insurance-pre-auth-multi-agent

**Status: completed**

Built a small Node.js multi-agent sample that reads pre-auth requests from an existing Azure DocumentDB cluster, runs a medical-review agent (LLM or deterministic fallback), generates an insurer submission letter, and persists the submission and status back to DocumentDB. The repository includes a seed script to create collections and sample data, a CLI entrypoint and an Express demo endpoint that trigger the orchestrator, unit tests that run offline via mocks, and a README with instructions. I verified the seed script, unit tests, and an end-to-end run of the orchestrator against the live cluster described in the run environment using the DOCUMENTDB_URI present in the environment.

## How to run

1) Install dependencies: npm install
2) Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY and CHAT_MODEL).
3) Seed the sample data: npm run seed
4) Run the orchestrator for a preauth id: node src/run-orchestrator.js --id=preauth-1
   Or start the demo server: node src/server.js and POST /preauth/:id/process
5) Run unit tests (no live DB required): npm test

## Verified by running

- npm install: succeeded (with mongodb dependency changed to ^5.8.0 to resolve an install error)
- jest tests: 2 passed (test/orchestrator.test.js) — local unit tests run and passed using mocks
- Seed script: node src/seed.js executed successfully and reported 'Seeding completed.'; it created collections and indexes in database sample_healthcare_08
- DocumentDB MCP inspection: documentdb_list_databases for sample_healthcare_08 returned collections preauth_requests (3), clinical_criteria (4), submissions (0) immediately after seeding
- End-to-end orchestrator run against live cluster: node src/run-orchestrator.js --id=preauth-1 completed; it loaded the preauth, ran the deterministic medical-review logic (no OPENAI_API_KEY set in environment), drafted a submission, stored it in submissions, and updated preauth_requests status to 'submitted'
- DocumentDB MCP sample documents: submissions collection inspected and contains the inserted submission document for preauth-1; preauth_requests document for preauth-1 shows status 'submitted' and lastSubmissionAt timestamp

## Not verified

- LLM integration with an actual OpenAI API key (OPENAI_API_KEY) was not executed in these verification steps because no OPENAI_API_KEY was set in the runtime environment. The code paths for LLM-based agents exist and were exercised only via deterministic fallbacks in the run above.
- Vector/embedding-based retrieval and a vector index were not created or verified. I intentionally did not add embeddings or a vector index because the sample uses textual criteria lookup by procedureCode and LLM (or fallback) for assessment; this avoids selecting an embedding model name/dimension and vector-index tuning parameters given the information gaps.
- No Bicep/Terraform IaC was provisioned or executed (intentional: run_policy forbids Azure resource changes and the run environment already provides a cluster).

## Open issues

None.

## Files

- `src/orchestrator.js`
- `src/run-orchestrator.js`
- `src/server.js`
- `.env.example`
- `README.md`
- `test/orchestrator.test.js`
- `package.json (updated mongodb dependency to ^5.8.0)`

