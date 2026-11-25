# 3. Build report: 06-credit-risk-multi-agent-scorer

**Status: completed**

Built a small Python sample app (sample_fintech_06) demonstrating a three-agent credit-risk pipeline that reads applicant docs from an Azure DocumentDB (MongoDB-compatible) cluster, computes a rule-based credit score with an optional LLM refinement, generates a human-readable explanation, and writes the score+explanation back into the applicant document. The project includes an idempotent seed script, a CLI runner, and pytest tests that exercise the pipeline in mock mode (no LLM credentials). I verified dependency installation, seeding, tests (mock mode) and inspected the live cluster documents via the documentdb MCP server.

## How to run

1) Create a Python venv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Provide secrets via .env (copy .env.example -> .env). Required: DOCUMENTDB_URI. Optional: OPENAI_API_KEY for real LLM usage.

3) Seed sample data (idempotent):
   python -m sample_fintech_06.seed

4) Run the pipeline (mock LLM mode):
   python -m sample_fintech_06.run --applicant-id applicant-1 --mock

   To attempt real LLM refinements (if you have OPENAI_API_KEY set):
   python -m sample_fintech_06.run --applicant-id applicant-1 --use-llm

5) Run tests (tests use mock LLM and the live cluster):
   pytest -q

## Verified by running

- pip install -r requirements.txt: completed (packages installed successfully)
- python -m sample_fintech_06.seed: completed (seeded 2 applicants)
- pytest -q: completed (1 passed: tests/test_pipeline.py::test_pipeline_mock_end_to_end)
- documentdb MCP: documentdb_find_documents on sample_fintech_06.applicants: completed (returned 2 documents; applicant-1 contains creditScore, creditScoreDetails, creditScoreExplanation written by the run/test)

## Not verified

- Real LLM scoring/explanation calls (OpenAI) were not executed because no OPENAI_API_KEY was available in the run environment. The sample supports real LLM usage if OPENAI_API_KEY is set; the actual LLM results and any JSON parsing from the model were not verified.
- No additional indexes were created or validated beyond the default _id index (the sample uses equality queries by applicant id). Index change operations were not performed because they are unnecessary for the minimal sample and to avoid write operations to management plane resources.
- No infrastructure provisioning (Bicep/Terraform/Azure CLI) was attempted because the run policy forbids creating Azure resources. The sample expects a pre-provisioned DocumentDB cluster and reads DOCUMENTDB_URI at runtime.

## Open issues

- If you want end-to-end LLM-powered scoring in this environment, supply OPENAI_API_KEY (or configure Azure OpenAI credentials and modify the code accordingly).
- The sample currently uses a mock LLM mode for tests and local verification. If you plan to exercise real LLMs, you may want to harden parsing of LLM JSON responses and add stricter error handling and validation for model outputs.
- Consider adding a small index or TTL fields if you expand the sample to larger datasets or additional query patterns; for this minimal sample, default indexing is sufficient.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `sample_fintech_06/__init__.py`
- `sample_fintech_06/db.py`
- `sample_fintech_06/agents.py`
- `sample_fintech_06/seed.py`
- `sample_fintech_06/run.py`
- `tests/test_pipeline.py`

