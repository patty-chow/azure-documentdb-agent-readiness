# 3. Build report: 05-appointment-scheduling-assistant

**Status: completed**

Built a small Node.js sample appointment-scheduling assistant that demonstrates using Azure DocumentDB (MongoDB wire protocol) for provider availability slots and appointments. The sample includes a seed script that idempotently creates collections, sample slots and an appointment, domain operations that perform atomic booking/rescheduling/cancellation (using MongoDB conditional updates and transactions), a minimal LangChain-based agent wrapper (ChatOpenAI + BufferMemory + simple tools), an Express /chat endpoint, and a demo verification script that exercises the booking/reschedule/cancel flows against the live cluster. I verified dependency installation, seeding, and the demo verification flow against the live DocumentDB cluster and inspected the created collections and indexes through the documentdb MCP server.

## How to run

1) Copy .env.example to .env and fill DOCUMENTDB_URI (mongodb+srv style), OPENAI_API_KEY (if you want to run the agent), and optionally DATABASE_NAME and PORT.
2) Install dependencies: npm install
3) Seed the database (idempotent): npm run seed
4) Verify data-plane behaviors (find slots, create appointment, reschedule atomically, cancel): npm test
5) (Optional) Start the server: npm start — then POST JSON {"userId":"<id>", "message":"<text>"} to http://localhost:3000/chat

Notes: The agent uses an in-memory BufferMemory and the OpenAI chat model. To exercise the conversational agent you must set OPENAI_API_KEY in your .env. See README.md for details.

## Verified by running

- npm install: 0 exit code; dependencies installed.
- seed script (node src/seed.js): ran and printed 'Seeding complete. Inserted slots: 5 and 1 appointment.'
- demo verification script (npm test -> node src/demo_seed_verify.js): ran and executed the sequence: found available slots, created an appointment atomically, rescheduled the appointment atomically to a different available slot, and cancelled the appointment. Output included created appointment id and reschedule/cancel confirmations.
- documentdb_list_databases (via MCP) for database 'sample_healthcare_05': returned collections ['slots' (count 5), 'appointments' (count 2)].
- documentdb_list_indexes on 'slots' collection: indexes present: _id_ and compound index { providerId:1, start:1, status:1 } (name 'provider_start_status_idx').
- documentdb_list_indexes on 'appointments' collection: indexes present: _id_ and { patientId:1, createdAt:-1 } (name 'patient_createdAt_idx').

## Not verified

- Live conversational agent behaviour via the /chat endpoint using the OpenAI model was not fully exercised in automated verification because an OPENAI_API_KEY may not have been provided to the environment. The agent code (src/agent.js) is present and will run when OPENAI_API_KEY and model name are set, but I did not perform an end-to-end LLM-driven chat test.
- Persistent conversation memory (durable storage-backed memory) was not implemented or tested. The sample uses LangChain's BufferMemory (in-memory) for simplicity; persistence across process restarts was not verified because it was not implemented.
- No unit tests with mocked MongoDB driver were run. The sample includes a runtime data-plane verification script that exercised the real cluster; offline unit tests with mocks were not added.

## Open issues

- The agent's LLM-driven parsing convention expects the model to return strict JSON indicating which tool to call. This keeps the example small but is brittle in production; a production agent should use a robust agent executor and safer parsing/validation of model outputs.
- Memory is ephemeral (in-memory BufferMemory); the sample documents this but does not implement persistence. Consider adding a DocumentDB-backed or Redis memory store for real deployments.
- The sample currently assumes the environment variable DOCUMENTDB_URI points to a reachable DocumentDB cluster with the MongoDB wire protocol. Ensure you do not run seeding against a production cluster.
- If you want to run the conversational endpoint in CI or automated tests, add either a mock of the OpenAI API or a test LLM shim and add unit tests that mock the mongodb driver.

## Files

- `package.json`
- `package-lock.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `src/db.js`
- `src/seed.js`
- `src/store.js`
- `src/agent.js`
- `src/server.js`
- `src/demo_seed_verify.js`

