Personalized Content Selection — Azure DocumentDB sample

This repository contains a small Node.js sample that demonstrates a retrieval-augmented personalized content selection flow using Azure DocumentDB (MongoDB-compatible). It seeds a small sample dataset into the provided cluster, creates a vector index (cosmosSearch), and exposes a minimal HTTP API to request personalized content for a customer.

Key points
- Node.js (Express) app with a simple in-process agent that uses customer profile, segment and recent interactions to build a query embedding, performs nearest-neighbour retrieval over stored embeddings (application-side cosine similarity for the sample), and returns a ranked list with rationale.
- The app creates a cosmosSearch vector index (vector-hnsw) on the content_pieces collection during seeding so developers can inspect the index with the documentdb MCP tools.
- The sample uses a deterministic "mock" embedding generator by default so it runs without external API keys. You can configure a real embedding provider by setting EMBEDDING_PROVIDER and EMBEDDING_DIM in .env.

Prerequisites
- Node.js 24+ (Node 20+ should also work)
- An Azure DocumentDB cluster reachable from this machine. Its connection string must be set in DOCUMENTDB_URI in a local .env file.
- The run environment used to build this sample had a documentdb MCP server; the app itself only needs the mongodb connection string.

Files
- src/ - application source
  - db.js - MongoClient singleton
  - seed.js - idempotent seeding of sample data, collections and vector index
  - server.js - Express HTTP API with /search endpoint
  - agent.js - retrieval + ranking + rationale generation (mock chat)
  - run_sample.js - run a sample query in-process
- .env.example - example env file

How to run
1. cp .env.example .env and fill DOCUMENTDB_URI
2. npm install
3. npm run seed   # creates collections, index, and uploads sample docs
4. npm start     # starts HTTP API on PORT (default 3000)
5. In another shell: curl "http://localhost:3000/search?customerId=cust_1"

Cleanup
- The sample does not delete the database automatically. Use the documentdb MCP server or the portal to remove the sample_customer_360_14 database when finished.

Extending to real providers
- To use real embeddings, implement EMBEDDING_PROVIDER logic in src/agent.js and set EMBEDDING_DIM to the model's dimensions. The seed script uses EMBEDDING_DIM when creating the vector index.

Notes
- This sample intentionally keeps things small and simple for learning. Production apps should use server-side kNN ($search) with a proper vector index, external LLM providers for generation, secure secret management, and robust error handling.
