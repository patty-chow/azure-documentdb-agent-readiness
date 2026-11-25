Telehealth Session Summarizer (Azure DocumentDB sample)

This sample ingests a telehealth session transcript, builds a structured clinical summary (chief complaint, assessment, plan, follow-up) using an LLM, and stores the result in Azure DocumentDB (MongoDB-compatible cluster) in the `sample_healthcare_14` database.

What the sample shows
- A simple Python function summarize_transcript(transcript, patient_id) that returns a structured summary and saves it to the `clinical_summaries` collection.
- Minimal CLI and FastAPI endpoint to demo the flow.
- Idempotent seed script to create a synthetic patient and transcripts.
- Index creation for patientId lookup (created during seeding via MCP tool when available).

Prerequisites
- Python 3.10+ on PATH
- An Azure DocumentDB (MongoDB wire protocol) connection string in DOCUMENTDB_URI env var (see .env.example)
- (Optional) OpenAI API key in OPENAI_API_KEY to use the LLM; if absent the sample uses a simple rule-based fallback summariser.

Quick start
1. Create and activate a virtualenv
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
2. Install dependencies
   pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI and OPENAI_API_KEY (optional)
4. Seed sample data
   python scripts/seed.py
5. Run CLI demo
   python scripts/summarize_cli.py --patient-id patient_1 --transcript "Patient complains of headache and nausea..."
   This prints the summary and inserts it into `clinical_summaries`.

Security & PHI
- Do NOT use real patient data when trying this sample in public or shared environments.
- The sample reads secrets from environment variables; do not commit your .env file.

Extending with embeddings and vector search
- This sample does not create a vector index by default. See src/db.py and README comments for an example cosmosSearch vector index definition. If you want to enable embeddings, pick EMBEDDING_MODEL=text-embedding-3-small (1536 dims) and create a vector index with matching dimensions (vector-diskann recommended for M30 clusters).

Files
- src/db.py: MongoClient singleton and index creation helpers
- src/summarizer.py: summarize_transcript implementation (LLM + fallback)
- scripts/seed.py: seed patient and transcripts (idempotent upserts)
- scripts/summarize_cli.py: CLI wrapper
- .env.example: environment variable placeholders

License: MIT
