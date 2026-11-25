Azure DocumentDB Chargeback Dispute Multi-Agent Sample

This sample demonstrates a Node.js (Express) LangChain multi-agent system that orchestrates a chargeback dispute flow using Azure DocumentDB (MongoDB-compatible).

What it shows
- An orchestrator receives a claim and dispatches to:
  - Evidence agent: fetches transactions and communications from DocumentDB
  - Policy agent: reasons over evidence using an LLM to recommend accept/reject
  - Decision agent: writes the final outcome back to DocumentDB

Prerequisites
- Node.js 24+, npm
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment (do NOT commit secrets).
- If using LLMs/embeddings: set OPENAI_API_KEY (or change the LLM provider in code).

Setup
1. cp .env.example .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY if you will use the policy agent.
2. npm install
3. npm run seed   # idempotent: creates database, collections, indexes and sample documents
4. npm start

Endpoints
- GET /health
- POST /claims/:claimId/decide  -> triggers the orchestrator for claimId

Tests
- npm test   # unit tests use mocks so they run without a live cluster/LLM

Notes and design decisions
- Database: sample_fintech_18 (per prompt)
- Collections: transactions, communications, claims, decisions
- Connection string is read from DOCUMENTDB_URI and used by a singleton MongoClient (documentdb-driver guidance)
- Indexes: single-field indexes on claimId and transactionId for fast lookups
- Vector/semantic search: omitted by default; README documents how to add a vector index if you choose embeddings (choose an embedding model and match dimensions)

Cleanup
- Remove sample documents via the portal or by running a custom cleanup script (not provided to avoid accidental deletes).

Security
- Do not commit secrets. Use environment variables.

License: MIT
