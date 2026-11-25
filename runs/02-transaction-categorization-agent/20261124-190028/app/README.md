Azure DocumentDB sample: Transaction Categorization Agent

Overview
- A minimal Node.js (Express) app that demonstrates using a LangChain-backed LLM to categorize uncategorized transactions stored in an Azure DocumentDB (MongoDB-compatible) cluster. It writes categories back to documents and exposes an aggregation endpoint that returns monthly spend by category.

What it shows
- Singleton MongoClient usage for Azure DocumentDB
- Prompt-engineered LLM calls via LangChain/OpenAI
- Seed script (idempotent upserts) to populate sample data
- An HTTP endpoint GET /monthly-spend returning per-month per-category totals
- An endpoint POST /run-categorization which runs the agent over uncategorized transactions

Prerequisites
- Node.js 24+, npm
- An Azure DocumentDB cluster reachable from this machine. Set its connection string in DOCUMENTDB_URI env var. The environment this sample was built on had DOCUMENTDB_URI already set.
- An OpenAI API key in OPENAI_API_KEY

Setup
1. cp .env.example .env and fill DOCUMENTDB_URI and OPENAI_API_KEY
2. npm install
3. npm run seed   # seeds sample data and creates the index
4. npm start      # starts Express server on PORT (default 3000)

Usage
- POST http://localhost:3000/run-categorization  (triggers categorization of uncategorized transactions)
- GET  http://localhost:3000/monthly-spend       (returns JSON with monthly totals grouped by category)

Notes and constraints
- This sample reads the connection string and API keys from environment variables. Do NOT commit secrets.
- The code creates a compound index on { date: 1, category: 1 } to help aggregation.

Cleanup
- Delete the sample documents from the transactions collection or drop the collection in the sample_fintech_02 database.

License: MIT
