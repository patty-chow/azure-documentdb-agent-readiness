DocumentDB Product Recommendations Sample

Overview

This sample demonstrates a small Node.js app that:
- Connects to an existing Azure DocumentDB (MongoDB wire protocol) cluster using the mongodb driver.
- Ingests synthetic product and order data (20,000 orders) into a database named `sample_retail_02`.
- Generates product embeddings (using OpenAI when OPENAI_API_KEY is present, otherwise deterministic synthetic embeddings).
- Creates a DiskANN vector index on the products collection and stores embeddings on each product document.
- Serves a simple web UI that accepts a product ID and returns the top-5 recommended products plus natural-language reasoning (using OpenAI LLM when available, otherwise templated reasoning).
- Uses a 'sessions' collection in DocumentDB to persist per-session memory and personalise recommendations.

Prerequisites

- Node.js 24+ installed
- An Azure DocumentDB cluster reachable with a connection string in the DOCUMENTDB_URI environment variable
- (Optional) OPENAI_API_KEY for real embeddings and LLM reasoning

Setup

1. Copy .env.example to .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if available).
2. npm install
3. npm run seed   # this ingests products and 20,000 orders; may take a few minutes
4. npm start
5. Open http://localhost:3000 and try recommending for a product (product IDs are P0..P9999)

Notes

- The seed script will create three collections in sample_retail_02: products, orders, sessions.
- The sample will create a DiskANN vector index for the products collection. No Azure resource provisioning is performed — the app uses the existing cluster you point it at.
- For reproducibility, if OPENAI_API_KEY is not set, embeddings and LLM reasoning are deterministic synthetic values.

Files

- src/db.js: MongoDB singleton client
- src/seed.js: data ingestion (products, embeddings, orders)
- src/server.js: Express server, recommendation endpoint, session memory
- public/: static UI files

Security

Do not commit your real DOCUMENTDB_URI or OPENAI_API_KEY. Use environment variables.

License

MIT
