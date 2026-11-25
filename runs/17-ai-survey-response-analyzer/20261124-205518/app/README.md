Survey Response Analyzer — Beanie + Azure DocumentDB sample

Overview

This sample shows a small Python pipeline that:
- Seeds example survey response documents into an Azure DocumentDB cluster
- Uses a Beanie ODM model to enrich documents with themes, sentiment, a representative quote, and an embedding
- Stores embeddings as numeric arrays suitable for a native DocumentDB vector index
- Runs aggregation queries to show top themes and sentiment distribution per question

Prerequisites

- Python 3.10+ (the run environment uses a virtualenv)
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in .env
- (Optional) OPENAI_API_KEY for LLM/embedding calls. If absent, the pipeline runs a deterministic local fallback for verification.

Setup

1. Copy .env.example to .env and fill in DOCUMENTDB_URI (and OPENAI_API_KEY if available).
2. Create a virtualenv and install dependencies:
   pip install -r requirements.txt

Run

1. Seed sample data:
   python seeds/seed.py

2. Enrich documents (will use OpenAI if OPENAI_API_KEY is set, otherwise a deterministic local fallback):
   python enrich/enrich.py

3. Show aggregation reports:
   python aggregates/show_aggregates.py

Clean up

- Remove seeded documents by dropping the `survey_responses` collection in the `sample_customer_360_17` database.

Notes

- The code reads all configuration from environment variables. Do not hard-code secrets.
- The sample creates indexes using the DocumentDB MCP server where possible and documents the expected vector index shape in README. Creating a native vector index may require Azure roles and might be done manually in the portal; the sample attempts to create a vector index via the MCP tool during verification and records the result in the build report.
