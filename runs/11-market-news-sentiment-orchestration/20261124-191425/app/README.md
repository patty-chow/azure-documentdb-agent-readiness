Market News Sentiment Orchestration Sample

What this sample shows
- A Node.js (LangChain) orchestration that: scrapes Reuters finance headlines, calls an OpenAI LLM to score sentiment and extract ticker symbols, stores scored articles in an Azure DocumentDB (MongoDB wire) database `sample_fintech_11.sentiment_signals`, and posts a webhook alert if any extracted ticker matches an entry in the `watchlist` collection.

Prerequisites
- Node.js 24+, npm
- A reachable Azure DocumentDB cluster (MongoDB wire protocol). Set DOCUMENTDB_URI in environment.
- An OpenAI API key, set OPENAI_API_KEY in environment.
- (Optional) WEBHOOK_URL and WEBHOOK_TOKEN to receive watchlist notifications.

Setup
1. Copy .env.example to .env and fill in values (DO NOT commit secrets).
2. npm install

Run the demo
- npm run demo
  The demo will:
  - create collections and indexes if missing
  - scrape a small batch of headlines
  - call the LLM to analyze each headline
  - insert the scored document into sample_fintech_11.sentiment_signals
  - upsert a demo watchlist entry for AAPL and POST to WEBHOOK_URL if a match occurs

Notes and design choices
- LLM provider: OpenAI via OPENAI_API_KEY (chosen for portability and LangChain support).
- News source: Reuters Business/Finance RSS feed (public RSS; no API key required).
- Webhook auth: simple Bearer token provided in WEBHOOK_TOKEN (if set) — a lightweight choice suitable for demos.
- Indexes: the app creates an index on tickers (multikey), timestamp (recent-first), and a text index on headline. These are created idempotently at startup.

Security
- Secrets must be provided via environment variables. No secrets are written to files by the sample.

Cleaning up
- To remove inserted demo documents: connect to your cluster and drop or clean the `sentiment_signals` and `watchlist` collections in database `sample_fintech_11`.

Limitations
- This is a small demo: the LLM prompt and parsing are simple and not production hardened. Ticker extraction should be improved for real workloads.
