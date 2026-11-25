# Product Q&A Chatbot (LlamaIndex + Azure DocumentDB)

This sample demonstrates a simple Retrieval-Augmented Generation (RAG) chatbot using LlamaIndex in Python with Azure DocumentDB as the vector store.

What it shows
- How to connect to an existing Azure DocumentDB cluster via the DOCUMENTDB_URI environment variable
- How to seed a small synthetic product dataset and chunk product text for vector storage
- How to store chunk documents in a `product_chunks` collection and (optionally) compute/store embeddings
- A simple CLI REPL (python app.py) that retrieves the top-5 relevant chunks and generates a grounded answer

Important notes
- Do NOT put secrets or connection strings into files. Read the DocumentDB connection string from DOCUMENTDB_URI at runtime.
- This sample does NOT provision Azure resources. Use an existing cluster and the `sample_retail_13` database as required by the exercise.

Prerequisites
- Python 3.10+
- An Azure DocumentDB cluster reachable from this machine. Put its connection string in DOCUMENTDB_URI in a .env file.
- (Optional) An OpenAI API key in OPENAI_API_KEY if you want the sample to compute real embeddings and use OpenAI for generation.

Quick start
1. Create and activate a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows

2. Install dependencies
   pip install -r requirements.txt

3. Copy .env.example to .env and edit values
   cp .env.example .env
   # Edit .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if available)

4. Seed sample data into the cluster
   python seed.py --skip-embeddings
   # If you have OPENAI_API_KEY and want embeddings computed, omit the flag

5. (Optional) Create a vector index in DocumentDB (dimensions must match embedding model). The sample uses 1536 dimensions by default. See infra/README for an example create-index command.

6. Run the CLI chatbot
   python app.py

Success criteria
- seed.py inserts documents into the `sample_retail_13` database (`products` and `product_chunks` collections)
- Running app.py and asking a product question returns a grounded answer and shows the top-5 retrieved chunk ids (or shows fallback text-search results if embeddings/index unavailable)

Files of interest
- app.py — CLI REPL chat loop
- seed.py — Seed script that inserts products and chunk documents (optionally computes embeddings)
- db.py — MongoDB client singleton and helper functions
- utils.py — Text chunking utilities
- data/sample_products.json — synthetic sample products
- .env.example — example env variables

Security and costs
- The sample reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment; never check those into source control.
- Creating vector indexes and storing embeddings may incur costs on your DocumentDB cluster and OpenAI usage if you compute embeddings. Keep the sample dataset small for demos.

Non-goals
- This is a small sample for learning. It does not implement authentication, production-grade error handling, advanced prompt-engineering, nor automated infra provisioning.
