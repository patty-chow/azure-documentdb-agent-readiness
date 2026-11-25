Symptom Triage Chatbot (LangChain RAG) sample for Azure DocumentDB

What this sample shows
- How to store text sections and normalized embeddings in an Azure DocumentDB collection
- How to create a server-side vector index (vector-diskann) using cosmosSearchOptions
- How to run k-NN retrieval with $search + cosmosSearch and use the retrieved contexts in a LangChain-powered response
- Safety guardrails: the assistant never issues a medical diagnosis and always recommends professional consultation

Prerequisites
- Python 3.10+ available as `python` and `pip` on PATH
- An Azure DocumentDB cluster reachable from this machine; put its mongodb+srv connection string into DOCUMENTDB_URI in a local .env file (see .env.example). Do NOT commit secrets.
- (Optional) OPENAI_API_KEY if you want production-quality embeddings and LLM responses. If omitted, the sample uses deterministic local fallbacks so you can verify behavior without external keys.

Quickstart
1. Create and activate a virtualenv (optional but recommended):
   python -m venv .venv
   source .venv/bin/activate   # bash/macOS
   .venv\Scripts\activate    # Windows

2. Install dependencies:
   pip install -r requirements.txt

3. Copy .env.example to .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if available).

4. Seed the sample data and create the vector index:
   python seed.py

5. Run the API server:
   uvicorn app:app --reload

6. Call the triage endpoint (example):
   POST http://localhost:8000/triage
   JSON body: {"symptoms": "I have a high fever and severe headache"}

Cleaning up
- The seed script is idempotent and writes to the database named `sample_healthcare_06` in your cluster. To remove the collection, you can use your usual MongoDB tools or the Azure Portal. The sample does not create Azure resources (clusters).

Security
- The code reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables and never writes secrets to disk.
- The sample corpus is synthetic and does not contain PHI. This sample is for demonstration only and not medical advice.
