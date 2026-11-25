Personalized Email Campaign Builder — Azure DocumentDB sample

What this sample shows
- How to fetch customer segment profiles from an Azure DocumentDB cluster (MongoDB wire protocol)
- How to inject segment context (purchase_history and preferences) into an LLM prompt to generate personalized email subject lines and body copy
- How to write the generated drafts into a campaigns collection in the sample_retail_08 database

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in your environment
- (Optional) OpenAI API key in OPENAI_API_KEY to enable real LLM generation. If not present, the sample uses a deterministic fallback for offline runs.

Setup
1. Copy .env.example to .env and fill DOCUMENTDB_URI (and optionally OPENAI_API_KEY).
2. npm install
3. npm run seed       # seeds sample_retail_08.segments with example segments and creates basic indexes
4. npm run generate -- --segmentId=seg-1   # generate a campaign for segment 'seg-1'

Files of interest
- src/client.js  — MongoDB client singleton
- src/seed.js    — idempotent seed script to insert sample segments and create indexes
- src/generate.js — small agent: fetch segment, prompt LLM (or fallback), insert campaign document

Security
- Secrets and connection strings are read from environment variables; do not check .env into source control.

Verification
- After running the generator, inspect the campaigns collection (db sample_retail_08 campaigns) to see inserted documents with fields {segmentId, segmentName, subject, body, rawOutput, createdAt}.
