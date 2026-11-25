Product Catalog with Vector Search (Azure DocumentDB)

This sample demonstrates storing product documents in an Azure DocumentDB cluster and performing semantic search by embedding text with OpenAI's text-embedding-ada-002. Embeddings are stored as BSON binary float32 vectors and a server-side IVF vector index is attempted; a client-side fallback ranking is provided.

Prerequisites
- Python 3.10+ and pip
- A reachable vector-capable Azure DocumentDB cluster. Set DOCUMENTDB_URI in the environment to the cluster connection string.
- (Optional) An OpenAI API key in OPENAI_API_KEY to compute embeddings at seed and at query time. If not present, the seed script will use precomputed embeddings included in this repo.

Files
- app.py: Flask app exposing /search
- seed.py: Loads sample products, computes or reads embeddings, inserts them into sample_retail_01.products, and attempts to create a vector (IVF) index
- data/sample_products.json: sample product documents
- data/sample_embeddings.json: precomputed embeddings for offline seeding
- requirements.txt: pinned Python dependencies
- .env.example: example env vars

Usage
1. Create a virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate   # on macOS/Linux
   .\.venv\Scripts\activate  # on Windows
   pip install -r requirements.txt

2. Set env vars (or copy .env.example to .env and fill in):
   export DOCUMENTDB_URI="<your connection string>"
   export OPENAI_API_KEY="<optional: your OpenAI key>"

3. Seed the database (creates collection, inserts documents, attempts to create an index):
   python seed.py

4. Run the Flask app:
   flask --app app run --port 5000

5. Search (example):
   curl -X POST http://localhost:5000/search -H "Content-Type: application/json" -d '{"q": "comfortable running shoes"}'

Notes and limitations
- The seed script attempts to create a server-side IVF vector index using a plausible createIndexes command. If the cluster rejects this command, the script will still insert documents; the README will note the failure and client-side ranking will still work.
- Embeddings are stored as BSON Binary float32 bytes per the prompt instruction. The /search endpoint unpacks these binaries to compute similarity locally when returning results.
- Never store secrets in this repo. Use environment variables or a .env file excluded from source control.

Cleaning up
- Remove inserted documents by connecting to the cluster and dropping the sample_retail_01 database or the products collection.

License
MIT
