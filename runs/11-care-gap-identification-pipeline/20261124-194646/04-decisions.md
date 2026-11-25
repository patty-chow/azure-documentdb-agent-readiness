# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 8 |
| model_default | 8 |
| operator | 3 |
| tool_result | 2 |
| skill | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:31:47+00:00

## D002 (build): I chose Python 3.10+ with a virtual environment.

- **Instead of:** Node.js/TypeScript; Python 3.10+ (venv)
- **Because:** The workspace and skills are Python-oriented and the sample will use LangChain and PyMongo; Python is the natural fit.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use current system python (assume Python 3.10 or 3.11) and a venv; write code compatible with Python 3.10+.' from the prompt review.
- **When:** 2026-11-25T08:32:05+00:00

## D003 (build): I chose pymongo >=4.0 (latest 4.x).

- **Instead of:** pymongo 3.x; pymongo >=4.0 (latest 4.x)
- **Because:** Modern pymongo 4.x matches DocumentDB skills and supports current MongoDB wire protocol features.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use PyMongo (pymongo >=4.0, e.g., latest 4.x) and follow documentdb-driver guidance' from assumptions.
- **When:** 2026-11-25T08:32:08+00:00

## D004 (build): I chose SCRAM via DOCUMENTDB_URI.

- **Instead of:** SCRAM via DOCUMENTDB_URI; Microsoft Entra ID (OIDC)
- **Because:** DOCUMENTDB_URI is provided in the run environment and is the simplest secure method for the sample.
- **Reason came from:** `skill`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T08:32:20+00:00

## D005 (build): I chose to use the existing cluster (DOCUMENTDB_URI) and not provision any Azure resources.

- **Instead of:** Provision new cluster via az/Bicep/Terraform; Use existing cluster DOCUMENTDB_URI and do not provision
- **Because:** Run policy forbids Azure resource changes and the environment provides an existing reachable cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'The developer machine has the MCP servers... A cluster is already provisioned... Do not provision a new cluster; use the existing cluster described in skill_md.'
- **When:** 2026-11-25T08:32:24+00:00

## D006 (build): I chose to embed last_visit_date inside the patients collection and keep a single patients collection for this sample.

- **Instead of:** Embed last_visit inside patients documents; Keep visits as separate collection
- **Because:** Embedding last_visit simplifies queries and seed data for a small sample app while still demonstrating aggregation patterns; it's appropriate for a read-heavy care-gap identification sample.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Create collections such as "patients" and "visits" (or embed last-visit in patients). Documents include patient_id, dob or age, diagnosis_codes (array), last_visit_date.'
- **When:** 2026-11-25T08:32:27+00:00

## D007 (build): I chose OpenAI provider with a mainstream chat model (gpt-3.5-turbo) and embeddings (text-embedding-3-small).

- **Instead of:** OpenAI (text-embedding-3-small + gpt-4o); OpenAI (text-embedding-3-small + gpt-3.5-turbo); Azure OpenAI
- **Because:** gpt-3.5-turbo is broadly available and less likely to be blocked in this environment than specialty models; text-embedding-3-small provides stable embeddings if needed. This choice reduces friction for users running the sample.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Default to a common provider (OpenAI) with embeddings (e.g., text-embedding-3-small) and a chat/completion model for reasoning.'
- **When:** 2026-11-25T08:32:30+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:35:45+00:00

## D009 (build): I chose Python 3.10+ as the language/runtime for the sample app.

- **Instead of:** Use Node.js; Use Python
- **Because:** The environment has Python available and the sample prompt asks for a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use current system python (assume Python 3.10 or 3.11) and a venv; write code compatible with Python 3.10+."
- **When:** 2026-11-25T08:36:03+00:00

## D010 (build): I chose PyMongo (pymongo >=4.0) as the MongoDB driver and will follow the documentdb-driver guidance (singleton MongoClient).

- **Instead of:** pymongo 3.x; pymongo >=4.x
- **Because:** PyMongo is the standard Python MongoDB driver and matches the documentdb-driver skill guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Use PyMongo (pymongo >=4.0, e.g., latest 4.x) and follow documentdb-driver guidance (singleton MongoClient)."
- **When:** 2026-11-25T08:36:06+00:00

## D011 (build): I chose to load the documentdb-connection skill to follow connection configuration guidance when creating the MongoClient.

- **Instead of:** Read documentdb-connection skill; Don’t load additional skills
- **Because:** To follow best-practices (pooling, timeouts) when instantiating MongoClient.
- **Reason came from:** `prompt`
- **Evidence:** Prompt instruction: "Where a skill covers an area, load it before you design it." documentdb-connection is relevant for connection pool/timeouts.
- **When:** 2026-11-25T08:36:13+00:00

## D012 (build): I chose OpenAI as the default LLM provider but will implement a deterministic fallback mode when OPENAI_API_KEY is not set so the sample runs without external LLM credentials.

- **Instead of:** Use OpenAI; Use Azure OpenAI; Allow fallback to local heuristic
- **Because:** Many users have OPENAI_API_KEY; adding a fallback ensures the sample can be run in environments without keys for verification.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Default to a common provider (OpenAI) ... Environment variables (e.g., OPENAI_API_KEY) will be used." Also readiness_report noted model choice gap.
- **When:** 2026-11-25T08:36:18+00:00

## D013 (build): I chose not to require vector indexes or embeddings for this sample; the agent will use aggregation pipelines and LLM reasoning (or a deterministic fallback) to prioritize and produce talking points.

- **Instead of:** Use vector search/embeddings; Don't use vectors
- **Because:** Simpler to keep sample focused on aggregation tool and prompt-engineering for guidelines; avoids embedding model choice and vector index creation tangles.
- **Reason came from:** `model_default`
- **Evidence:** Prompt: identify patients missing recommended screenings based on age, diagnosis, last-visit documents — achievable with aggregations and LLM. Readiness report: vector search optional; not necessary for care-gap logic.
- **When:** 2026-11-25T08:36:23+00:00

## D014 (build): I chose a simple data model: single 'patients' collection containing patient_id, name, dob, sex, diagnosis_codes, last_visit_date, contact. Seed script will populate synthetic records in database 'sample_healthcare_11'.

- **Instead of:** Embed visits collection (separate); Single patients collection with last_visit_date
- **Because:** Simpler for aggregation pipelines and sample seed; avoids needing to join collections for this sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Create collections such as 'patients' and 'visits' (or embed last-visit in patients)."
- **When:** 2026-11-25T08:36:40+00:00

## D015 (build): I chose to change imports in src/main.py to local module imports (from db import get_db) so running `python src/main.py` works for users following README.

- **Instead of:** Keep imports as package style and run python -m src.main; Change imports to local module imports (db, agent)
- **Because:** More convenient for users; avoids requiring `python -m` or PYTHONPATH tweaks.
- **Reason came from:** `tool_result`
- **Evidence:** User run instructions in README indicate running `python src/main.py`. Module import failure occurred when running that command.
- **When:** 2026-11-25T08:37:53+00:00

## D016 (build): I chose to use server-side $$NOW with $dateDiff to compute age and days_since_last_visit (avoids serialization/timezone issues).

- **Instead of:** Use Python 'now' injected into aggregation pipeline; Use server-side $$NOW and $dateDiff
- **Because:** Safer and avoids client-side datetime serialization problems across clusters. $dateDiff with $$NOW is available in MongoDB 5.0+ and supported by the cluster.
- **Reason came from:** `tool_result`
- **Evidence:** Error: 'unrecognized time zone identifier' when embedding Python datetime into pipeline; documentdb skills recommend using server-side date ops when possible.
- **When:** 2026-11-25T08:38:19+00:00

## D017 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:41:31+00:00

## D018 (build): I chose Python 3.10+ with PyMongo (pymongo >=4.x) and LangChain for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.10+ with PyMongo and LangChain
- **Because:** The sample prompt requested a Python LangChain agent; Python with PyMongo is the natural choice and matches available runtime.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: 'Use current system python (assume Python 3.10 or 3.11) and a venv; write code compatible with Python 3.10+.' and 'Use PyMongo (pymongo >=4.0)'.
- **When:** 2026-11-25T08:41:51+00:00

## D019 (build): I chose to use the DOCUMENTDB_URI environment variable with SCRAM credentials by default and provide instructions for optional Entra/OIDC usage in the README.

- **Instead of:** Use DOCUMENTDB_URI (SCRAM) from env; Use Microsoft Entra OIDC token
- **Because:** The run environment explicitly provides DOCUMENTDB_URI; it is simple and works without extra setup. Entra ID is documented but optional.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T08:41:54+00:00

## D020 (build): I chose to use the existing DocumentDB cluster (no provisioning) and not perform any Azure resource changes.

- **Instead of:** Provision a new cluster; Use existing cluster and no infra changes
- **Because:** Run policy forbids creating or changing Azure resources and a cluster is already available for use.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' and run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T08:41:56+00:00

## D021 (build): I chose two collections: 'patients' and 'visits' (normalized). 'visits' stores historical visit dates and types; 'patients' stores demographics and diagnosis codes.

- **Instead of:** Single collection with embedded visits; Two collections: patients and visits (normalized)
- **Because:** Normalized visits makes it easier to seed multiple visits per patient and run aggregation pipelines to compute last_visit_date; it's realistic for healthcare data modeling.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Create collections such as "patients" and "visits" (or embed last-visit in patients).'
- **When:** 2026-11-25T08:41:59+00:00

## D022 (build): I chose to not use vector search or embeddings for this initial sample; the agent will run DocumentDB aggregations to identify gaps and then use an LLM for prioritization and talking points. Vector search is optional and documented in README.

- **Instead of:** Use vector search and embeddings for prioritization; Use LLM reasoning (LangChain) over aggregation results without vectors
- **Because:** Keeps the sample simpler and avoids needing an embedding model and vector index configuration; achieves goals (identify gaps, prioritize, generate talking points).
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information_gaps: embedding model unspecified; and the prompt focuses on aggregation tool usage.
- **When:** 2026-11-25T08:42:04+00:00

## D023 (build): I chose OpenAI as the default LLM provider and 'gpt-4o-mini' as the default reasoning model, configurable via environment variables; the app will gracefully skip live LLM calls if no API key is present.

- **Instead of:** OpenAI provider with gpt-4 style model; OpenAI provider with gpt-4o-mini or similar; Local LLM
- **Because:** OpenAI is a common, widely available provider. Choosing a light model reduces cost during tests; but the code will be configurable and skip calls if key absent.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Default to a common provider (OpenAI) ... environment variables (e.g., OPENAI_API_KEY) will be used.'
- **When:** 2026-11-25T08:42:08+00:00
