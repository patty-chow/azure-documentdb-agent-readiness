Product Catalog with Vector Search (Azure DocumentDB sample)

This sample demonstrates a small product catalog stored in Azure DocumentDB with vector-based semantic search.

What it shows
- Storing product documents with embeddings packed as BSON binary vectors
- Creating a vector-ivf index (script provided)
- A Flask /search endpoint that accepts natural-language queries, embeds them, and returns top-k semantically similar products

Prerequisites
- Python 3.10+ (this repo was developed for Python 3.10+; your runtime may be newer)
- (Recommended) Run the DocumentDB local gateway Docker image: ghcr.io/documentdb/documentdb/documentdb-local:latest, listening on port 10260.
- OR: an Azure DocumentDB cluster (Microsoft.DocumentDB/mongoClusters) connection string set in MONGO_URI
- If you want real embeddings: set OPENAI_API_KEY to call OpenAI's text-embedding-ada-002. If not set, the sample uses a deterministic mock embedder for offline testing.

Files
- app.py: Flask app with /search endpoint
- scripts/load_data.py: Load sample data, compute embeddings, and insert into the products collection
- scripts/create_vector_index.py: Attempt to create a vector-ivf index (prints payload if server doesn't accept the command)
- data/sample_products.json: Small seed dataset
- requirements.txt: Python dependencies
- .env.example: Example environment variables

Quickstart (local gateway)
1. Start the DocumentDB local gateway (recommended):
   docker run -p 10260:10260 ghcr.io/documentdb/documentdb/documentdb-local:latest

2. Install dependencies:
   python -m pip install -r requirements.txt

3. Copy .env.example to .env and edit values if needed. Ensure MONGO_URI points to your gateway or cluster and (optionally) set OPENAI_API_KEY.

4. Load sample data (this will call the embedding provider or use a mock):
   python scripts/load_data.py --file data/sample_products.json

5. Create the vector index (this attempts a server-side command; if it fails the script prints the payload):
   python scripts/create_vector_index.py

6. Run the Flask app:
   python app.py

7. Example search (curl):
   curl -X POST -H "Content-Type: application/json" -d '{"q":"comfortable running shoes"}' http://localhost:5000/search

Notes
- The script stores embeddings as BSON Binary packed float32 (little-endian). The index creation payload demonstrates creating a cosmosSearch vector-ivf index with COS similarity. The exact admin command and options may depend on your DocumentDB cluster version; consult your cluster admin or the DocumentDB portal if the createSearchIndexes command fails.
- No secrets are stored in this repository. Provide MONGO_URI and OPENAI_API_KEY via environment variables or a .env file.

Cleaning up
- If you used a local gateway Docker container, stop/remove it.
- To delete sample documents from your cluster: use mongosh or the portal and drop the `product_catalog.products` collection.

Security and production
- This sample is a demo and is not production-hardened. For production see documentdb-security guidance: TLS, Private Endpoints, Entra ID, and RBAC.
