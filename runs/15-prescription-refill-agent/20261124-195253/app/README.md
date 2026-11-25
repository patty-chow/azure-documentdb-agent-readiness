Azure DocumentDB Prescription Refill Agent (sample)

This sample demonstrates a small Node.js agent that interacts with an Azure DocumentDB (MongoDB-compatible) cluster to:
- Look up a patient's active prescriptions
- Check refill eligibility (based on days supply remaining and refillCount)
- Create a refill request document
- Maintain simple agent memory so a follow-up like "refill my blood pressure medication" resolves to the previously referenced medication

Important constraints and choices
- Language / ODM: Node.js + Mongoose (Beanie is Python-only; see readiness report).
- Connection: read MongoDB connection URI from env var DOCUMENTDB_URI (do NOT commit secrets).
- Memory: agent memory persisted in collection `agent_memory`.
- LLM: the shipped agent uses a small rule-based fallback. The code is pluggable to call an LLM (OpenAI) if you set OPENAI_API_KEY.

Prerequisites
- Node.js 24+, npm
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in your environment to the cluster's MongoDB connection string. Use database `sample_healthcare_15` (the seed script targets this DB).

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI and PORT if desired.
2. Install dependencies: npm install
3. Seed the sample data and create indexes: npm run seed
4. Start the server: npm start
5. Example call (curl):
   curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{"patientId":"patient-1","message":"Please refill my lisinopril"}'

Files created
- src/: application code
  - src/db.js: Mongoose connection
  - src/models/: Mongoose schemas for prescriptions, refillRequests, agent memory
  - src/agent.js: small rule-based agent that implements the sample flows
  - src/index.js: Express HTTP API exposing /chat
- scripts/seed.js: idempotent seeding script that creates sample data and indexes
- .env.example, README.md, package.json

Security note
- This sample stores synthetic data only. Do NOT use this code as-is in production for PHI without appropriate encryption, auditing, and consent.

How it maps to the request
- The sample demonstrates the DocumentDB usage patterns recommended by the installed skills: singleton MongoClient (via Mongoose), TLS via connection string, index creation for query shapes, and a simple agent memory store backed by the DB.

Limitations / future work
- The agent is a minimal rule-based demonstrator rather than a LangChain-powered LLM agent to keep the sample runnable without requiring API keys. The code is structured so LangChain/OpenAI can be added by providing OPENAI_API_KEY and adding an LLM wrapper.
