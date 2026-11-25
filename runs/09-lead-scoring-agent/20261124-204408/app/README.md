Lead Scoring Agent (DocumentDB sample)

This sample shows a small Node.js LangChain-style agent that reads lead activity,
firmographics, and engagement signals from an Azure DocumentDB (MongoDB-compatible) cluster,
reasons over them, assigns a score (0-100), and writes the score and a one-paragraph
rationale back to the lead document.

Prerequisites
- Node.js 20+ (Node 24 recommended)
- A reachable Azure DocumentDB cluster; put its connection URI in DOCUMENTDB_URI
  in a local .env file (see .env.example). The sample uses database: sample_customer_360_09
- (Optional) OPENAI_API_KEY for better natural-language rationale generation. If not provided,
  the sample uses a deterministic heuristic so you can run it offline against the DB.

What the sample provides
- src/db.js — singleton MongoClient (uses mongodb@6.x)
- src/seed.js — idempotent seed script that creates collections, indexes, and sample documents
- src/scoreLead.js — CLI to score a lead and update the lead document
- src/server.js — small Express API with POST /score-lead to score a lead
- .env.example — placeholders for secrets

Quick start
1. cp .env.example .env and fill DOCUMENTDB_URI (and optionally OPENAI_API_KEY)
2. npm install
3. npm run seed            # loads sample data into sample_customer_360_09
4. npm run score -- --leadId=lead-1   # scores lead-1 and updates leads collection
5. npm start               # run HTTP API (POST /score-lead body: { "leadId": "lead-1" })

Notes about vector search and embeddings
- This sample chooses OpenAI text-embedding-3-small (1536 dims) as a plausible
  default for semantic embeddings. The seed script does NOT create a vector index
  automatically (vector index creation can be cluster-specific and requires
  special createIndexes with cosmosSearchOptions). README includes example commands
  for creating a vector index manually.

Security
- Never commit secrets. Use .env locally. This sample reads DOCUMENTDB_URI from env.

Cleanup
- Remove sample data via the DocumentDB tools or run a small script to drop the
  sample_customer_360_09 database (not included because destructive operations
  should be handled by the user).
