# Market News Sentiment Orchestration (Sample 11)

This sample shows a Node.js LangChain orchestration that:
- "Scrapes" financial news headlines (from a small bundled seed or external NewsAPI if configured)
- Runs a sentiment + ticker-extraction agent (OpenAI LLM by default)
- Stores scored articles in an Azure DocumentDB (MongoDB-compatible) cluster
- Runs an alert agent that looks up a watchlist in the DB and emits notifications for matches

Important: The sample reads the Database connection string from the environment variable `DOCUMENTDB_URI`. Do NOT commit real secrets to the repo. See `.env.example`.

Prerequisites
- Node.js 24+ (provided in the run environment)
- An Azure DocumentDB (MongoDB-compatible) cluster reachable from your machine. Set DOCUMENTDB_URI accordingly.
- (Optional) OPENAI_API_KEY for better sentiment/ticker extraction. If not provided the sample uses a simple rule-based sentiment scorer.

Quickstart
1. Install dependencies:
   npm install

2. Seed watchlist and sample headlines (idempotent):
   npm run seed

3. Run the orchestration once from the CLI:
   npm run run

4. Or start the minimal HTTP demo server and open GET /run:
   npm start
   # then visit http://localhost:3000/run

What the sample creates
- Database: sample_fintech_11
- Collections: articles, watchlist
- Indexes: text index on articles.headline, index on articles.tickers

Notes and limitations
- The repository does not include any real credentials. Provide them via environment variables.
- Vector index creation is not guaranteed in this environment; the sample stores embeddings when an embedding provider is available but creating vector indexes on the cluster may require manual steps. See the code and README for details.

Files
- src/: application source
- scripts/seed.js: idempotent seed script for watchlist and sample headlines
- .env.example: environment variables template

License: MIT
