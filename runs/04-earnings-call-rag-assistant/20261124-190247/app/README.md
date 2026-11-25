Earnings-call RAG sample using Azure DocumentDB (MongoDB wire protocol) and LlamaIndex

What this sample shows
- Ingests earnings-call transcripts (plain-text or PDF) into a DocumentDB collection
- Chunks text, computes embeddings (sentence-transformers 'all-MiniLM-L6-v2'), stores vectors in DocumentDB
- Creates a vector-diskann index matching the embedding dimension
- Runs a vector KNN retrieval ($search + cosmosSearch) against DocumentDB and returns top-k chunks
- Uses LlamaIndex/OpenAI (when available) to synthesize answers from retrieved passages and cites source+timestamp

Prerequisites
- Python 3.10+ (this environment uses Python 3.13)
- An Azure DocumentDB cluster reachable from this machine. Put its connection string into DOCUMENTDB_URI env var.
- (Optional) OPENAI_API_KEY if you want model-based answer synthesis

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env and edit DOCUMENTDB_URI (and OPENAI_API_KEY if you have one)
4. python src/ingest.py --source samples/earnings_call_sample.txt
   This will create the collection `earnings_chunks` in the `sample_fintech_04` database, create necessary indexes, and insert chunk documents.
5. python src/query.py --query "What did management say about Q2 revenue?" --k 3

Files
- src/ingest.py: ingest and index pipeline
- src/query.py: query/retrieve + answer synthesis
- src/db.py: MongoDB client helper (reads DOCUMENTDB_URI)
- samples/earnings_call_sample.txt: small placeholder transcript

Security
- Do NOT check in real secrets. Use environment variables (DOCUMENTDB_URI, OPENAI_API_KEY).

Notes and limitations
- This sample uses sentence-transformers locally for embeddings (dims=384). If you switch embedding models, update the vector index `dimensions` accordingly and rebuild indexes.
- The sample demonstrates creating a DocumentDB vector index using the documentdb MCP helper. The run environment should have access to the cluster and its MCP profile.

Cleanup
- Remove inserted documents and drop the `earnings_chunks` collection from the `sample_fintech_04` database using your normal Mongo tooling or the Azure portal.
