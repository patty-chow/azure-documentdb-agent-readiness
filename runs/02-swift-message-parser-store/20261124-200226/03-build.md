# 3. Build report: 02-swift-message-parser-store

**Status: completed**

Built an async Python sample that ingests simplified SWIFT MT103/MT202 messages into an Azure DocumentDB cluster (MongoDB-compatible) using Beanie + Motor, validates required fields, performs bulk writes for throughput, and exposes an aggregation pipeline (daily counts and total amounts per message_type). I seeded sample documents, created/ensured indexes, ran an aggregation query, and used the documentdb MCP tools to inspect indexes and sample documents. The FastAPI app and supporting scripts are included; the Beanie initialization was tested successfully. The SWIFT parser is intentionally simple and documented as a demo, not a production parser.

## How to run

1) Create and activate a Python venv. 2) Install dependencies: pip install -r requirements.txt. 3) Set DOCUMENTDB_URI in your environment (or copy .env.example to .env and edit it). 4) Ensure the database name sample_banking_02 is acceptable for your cluster. 5) Create indexes: python create_indexes.py. 6) Seed sample data: python seed.py. 7) (Optional) Start the HTTP API: uvicorn src.app:app --reload. 8) Ingest example messages via POST /ingest (JSON body {"messages": [ ... ]}). 9) Get aggregation via GET /aggregations/daily-summary.

## Verified by running

- pip install -r requirements.txt: exit code 0 (dependencies installed or already present).
- python create_indexes.py: exit code 0; output: 'Indexes ensured' (script is idempotent; first run logged an existing-index conflict and subsequent run succeeded).
- python seed.py: exit code 0; output: 'Inserted 4 documents' (seed script is idempotent and skipped duplicates).
- python scripts/aggregate_test.py: exit code 0; printed aggregation pipeline results from the live cluster (two groups returned; example rows were printed).
- documentdb_list_indexes (MCP tool) called for db 'sample_banking_02' / collection 'swift_messages': returned index list including _id_, message_id_1, message_type_1_value_date_1, ux_message_id (unique), ix_amount_desc.
- documentdb_find_documents (MCP tool) called for db 'sample_banking_02' / collection 'swift_messages': returned sample documents (total_count 6 returned_count 6) showing parsed tags and stored fields.
- Beanie initialization tested by running init_beanie in a short script (python -c ...): printed 'Beanie initialized' and closed the client successfully.

## Not verified

- Running the FastAPI server (uvicorn src.app:app --reload) and exercising the HTTP endpoints via curl/HTTP to demonstrate live API responses was not executed in this run (no long-running server was started).
- Automated pytest test suite was not run; there is a tests/ file present from the environment but tests were not executed.
- Full coverage / correctness of the SWIFT MT103/MT202 parsing (the parser is intentionally small and heuristic). This is a design choice documented in README; a production-grade parser was not implemented or verified against a canonical SWIFT test corpus because no canonical sample set was available in the environment.
- Exact pin compatibility validation of the chosen package ranges (beanie>=1,<2, motor>=3,<4, pymongo>=4,<5) against a specific Azure DocumentDB wire-version (MongoDB 7.0) was not exhaustively proven here beyond installing packages and running the sample. The readiness report noted this gap; the sample uses safe range constraints rather than strict micro-version pins.

## Open issues

- The included SWIFT parser is intentionally simplified (regex-based). It demonstrates ingestion and parsing but is NOT a full, standards-compliant SWIFT MT parser. The README documents this and shows the mapping assumptions used by the sample.
- Monetary amounts are stored as Python floats for simplicity in this sample; this loses precision for some financial workloads. For production, use Decimal / BSON Decimal128 and appropriate schema changes.
- The cluster already contained some documents and an existing index named message_type_1_value_date_1; create_indexes.py handled the name conflict but pre-existing data/indexes in the target cluster may affect sample idempotency and results.
- I did not provision or modify Azure control-plane resources (per run policy). The sample includes only code and scripts to connect to an existing cluster; if users want IaC, they must run their own Bicep/Terraform following the readiness guidance (not executed here).

## Files

- `.env.example`
- `README.md`
- `requirements.txt`
- `create_indexes.py`
- `seed.py`
- `scripts/aggregate_test.py`
- `scripts/init_beanie_test.py`
- `src/app.py`
- `src/db.py`
- `src/models.py`
- `src/parser.py`
- `LICENSE`

