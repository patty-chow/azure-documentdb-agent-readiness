Azure DocumentDB Identity Resolution sample

This sample demonstrates a simple Python + Beanie + LangChain multi-agent identity-resolution pipeline using Azure DocumentDB (MongoDB-compatible).

What it shows
- Seed script to generate synthetic profiles and embeddings
- Vector index creation (HNSW) on the profiles collection
- A match agent that finds candidate duplicates using vector search
- A merge agent that consolidates matched profiles into a golden record using an LLM
- An audit agent that records every merge decision with confidence and source refs

Prerequisites
- Python 3.13 on PATH
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI
- (Optional) OpenAI API key for embeddings and LLM steps; set OPENAI_API_KEY

Quickstart
1. pip install -r requirements.txt
2. Copy .env.example to .env and set environment variables (DOCUMENTDB_URI required)
3. python -m src.seed_data    # creates collections, sample data, and vector index
4. python -m src.run_orchestrator --sample-size 10   # run the orchestrator on a subset

Notes
- The sample reads credentials and keys from environment variables. Do NOT store secrets in code.
- If OPENAI_API_KEY is not set, the seed script synthesizes random embeddings so the sample can run without networked LLMs.

License: MIT
