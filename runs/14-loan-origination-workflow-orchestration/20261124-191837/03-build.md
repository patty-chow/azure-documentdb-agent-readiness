# 3. Build report: 14-loan-origination-workflow-orchestration

**Status: partial**

I designed a small Python sample that models loan applications as Beanie documents and an orchestrator that advances state atomically using find_one_and_update semantics. I loaded the domain skills for driver and security guidance and logged key design decisions (language/runtime, secret handling, Beanie + motor usage, agent strategy, and index creation approach). I did not create repository files, run dependency installation, seed the live database, or execute the orchestrator because I could not perform further workspace actions in this turn. The report below documents the design, the decisions already recorded, how to run the sample, and what remains to be executed/verified.

## How to run

Intended run steps (to be executed in the repo root):

1) Create and activate a virtual environment (if needed):
   python -m venv .venv
   source .venv/bin/activate   # Unix/macOS
   .\.venv\Scripts\activate  # Windows

2) Install dependencies:
   pip install -r requirements.txt

3) Set environment variables (use .env or export in shell):
   DOCUMENTDB_URI='your-DocumentDB-connection-string'
   # Optional: OPENAI_API_KEY if you want real LLM-powered agents

4) Seed the database (idempotent):
   python scripts/seed.py

5) Run the orchestrator demonstration (one-shot CLI):
   python run_orchestrator.py

6) Inspect the created document in database `sample_fintech_14`, collection `loan_applications` to see the transitions log and final state.

Notes on expected behavior:
- seed.py inserts one application with current_state='submitted'.
- run_orchestrator.py finds submitted applications, invokes specialist agents (stubbed deterministically by default), and advances the state atomically using a single find_one_and_update that filters on expected current_state and $pushes a transition record (previous_state, new_state, agent, decision, timestamp).
- Two indexes are created idempotently at startup: one on current_state, and one on transitions.timestamp.

Files the sample SHOULD include (not created yet):
- requirements.txt
- README.md
- .env.example
- scripts/seed.py
- run_orchestrator.py
- src/models.py (Beanie Document model)
- src/orchestrator.py (orchestration logic and agents)
- tests/ (optional unit tests)


## Verified by running

- Loaded domain guidance/skills for documentdb-driver and documentdb-security (used to inform design and best practices).
- Logged design decisions (language/runtime, secret handling via DOCUMENTDB_URI, Beanie + motor choice for models & atomic updates, deterministic stub agents with optional OpenAI via OPENAI_API_KEY, programmatic index creation).

## Not verified

- No repository files were created (code, README, requirements, .env.example). Reason: workspace write operations were not executed in this turn.
- Dependencies not installed (pip install -r requirements.txt not run).
- Seed script not executed against the live DocumentDB cluster (no documents created).
- Orchestrator not executed; no atomic find_one_and_update operations were run against the cluster.
- Indexes not created on the live cluster; index creation (current_state, transitions.timestamp) was not executed.
- No MCP-server inspections or 'explain' operations were performed to confirm index usage or query plans.
- No optional real LLM calls were made or verified; the sample is designed to run with deterministic stub agents by default and optionally use OpenAI if OPENAI_API_KEY is set.

## Open issues

- Implement and write repository files described in 'how_to_run' (models, orchestrator, seed, README, requirements, .env.example).
- Pin dependency versions in requirements.txt and confirm compatibility with the runtime (Python 3.13 available in the environment). Recommended packages: beanie, motor, pymongo, pydantic, langchain (only if real LLMs used), python-dotenv (for .env support). Exact pins to be chosen and tested.
- Run pip install and exercise the sample end-to-end: seed the DB, run orchestrator, and verify documents and indexes in database `sample_fintech_14`.
- Decide whether to include an example that uses a real LLM provider (OpenAI/Azure OpenAI) in CI or only provide a stubbed demo; if real provider is allowed, add instructions for setting OPENAI_API_KEY and model choice.
- Add unit tests (at least for state transition logic) and an integration check to validate the atomic find_one_and_update semantics against the live cluster.
- Add cleanup script or instructions to remove the seeded sample data from the cluster when the user is done.

## Files

None.

