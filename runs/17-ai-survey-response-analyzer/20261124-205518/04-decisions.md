# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| tool_result | 5 |
| readiness_report | 4 |
| operator | 2 |
| model_default | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:16:07+00:00

## D002 (build): I chose Python 3.11 (Beanie ODM) for the sample implementation.

- **Instead of:** Node/JS; Python
- **Because:** The prompt requested a Python pipeline using Beanie ODM; Python with Beanie is the natural choice and matches the run environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: "Use a modern Python 3.11 (or 3.10) virtualenv; rely on pip/venv as in skill_md."
- **When:** 2026-11-25T12:16:33+00:00

## D003 (build): I chose Beanie ODM (async) with Motor as the async driver for DocumentDB access.

- **Instead of:** Beanie + Motor async stack; PyMongo AsyncMongoClient + hand-rolled models
- **Because:** Prompt explicitly required Beanie; Motor is Beanie's supported async driver.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: "Decide the Python async stack before coding: either pin Beanie + Motor to versions ... or use PyMongo's AsyncMongoClient"
- **When:** 2026-11-25T12:16:36+00:00

## D004 (build): I chose OpenAI (hosted) for embeddings and LLM calls, with a deterministic local fallback when OPENAI_API_KEY is not set.

- **Instead of:** OpenAI (hosted) embeddings & LLM; Azure OpenAI Service; Local mock/fallback
- **Because:** OpenAI is a common, well-supported choice and keeps the sample minimal; the fallback ensures the sample can be verified without keys.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: "Builder will use a hosted LLM + embedding provider (commonly OpenAI), with API key read from environment variables (e.g., OPENAI_API_KEY)."
- **When:** 2026-11-25T12:16:54+00:00

## D005 (build): I chose Motor as the async driver because Beanie requires Motor for its ODM integration; this keeps the sample consistent with Beanie usage.

- **Instead of:** Motor (async driver for Beanie); PyMongo AsyncMongoClient (new preferred async)
- **Because:** Beanie currently integrates with Motor; using Motor avoids rewriting Beanie internals. I acknowledge the documentdb-connection skill recommends PyMongo Async for new projects, but the prompt mandates Beanie.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Beanie + Motor to versions you have validated against the cluster" and documentdb-connection note about PyMongo async deprecation guidance.
- **When:** 2026-11-25T12:17:09+00:00

## D006 (build): I chose to attempt creating indexes via the documentdb MCP server and, upon failure, to fall back to documenting the index shapes and create only application-level indexes if possible.

- **Instead of:** Create indexes via documentdb MCP server; Do not create indexes programmatically; document expected indexes in README
- **Because:** The MCP create index tool failed; rather than blocking, the sample will continue and record the failure in the build report and README, and provide index definitions for manual application.
- **Reason came from:** `tool_result`
- **Evidence:** Attempt to call documentdb_create_index for collection survey_responses returned an error.
- **When:** 2026-11-25T12:18:13+00:00

## D007 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:19:56+00:00

## D008 (build): I chose Beanie ODM pinned to beanie==1.24.0 with Motor==3.1.1 and PyMongo==4.6.0 (as in requirements.txt).

- **Instead of:** Use PyMongo AsyncMongoClient (pymongo Async) with hand-written models; Use Beanie ODM built on Motor (async) as the prompt requested
- **Because:** The user explicitly requested a Beanie-based pipeline; keeping Beanie ensures the sample matches the prompt and is simpler for readers. Although documentdb-connection recommends PyMongo Async, Beanie's Motor support allows fulfilling the prompt. I recorded this tradeoff.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will create a Beanie Document model' from prompt review and existing repository files that already use Beanie and Motor.
- **When:** 2026-11-25T12:20:38+00:00

## D009 (build): I chose to read DOCUMENTDB_URI from an environment variable and include .env.example with placeholders.

- **Instead of:** Read connection string from a secrets manager or hard-code for demo; Read connection string from environment variable DOCUMENTDB_URI at runtime
- **Because:** This follows the run environment guidance and security best practices to avoid committing secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'The connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into a file.'
- **When:** 2026-11-25T12:20:41+00:00

## D010 (build): I chose NOT to provision any Azure resources programmatically; the sample will use the existing cluster described in the run environment and will provide IaC files as examples only if necessary.

- **Instead of:** Provision Azure DocumentDB cluster via az/bicep from sample; Do not provision resources; use existing cluster and document instructions
- **Because:** Policy forbids resource creation; using the existing cluster avoids unnecessary actions and matches environment assumptions.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' and readiness_report noting a live cluster is available.
- **When:** 2026-11-25T12:20:51+00:00

## D011 (build): I chose to make OpenAI optional and fall back to a deterministic local extractor/embedding when OPENAI_API_KEY is not set; the code will use OPENAI if provided.

- **Instead of:** Use OpenAI (hosted) for LLM and embeddings by default; Use local deterministic fallback when OPENAI_API_KEY missing
- **Because:** This ensures the sample can be run without external API keys for verification while supporting real LLMs if keys are available.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use a hosted LLM + embedding provider (commonly OpenAI)... make configurable via env.' Also enrich/enrich.py contains this pattern already.
- **When:** 2026-11-25T12:21:10+00:00

## D012 (build): I chose text-embedding-3-small (1536 dimensions) as the default embedding model, configurable via OPENAI_MODEL_EMBEDDING and EMBEDDING_DIMENSIONS environment variables.

- **Instead of:** Use OpenAI text-embedding-3-small (1536 dims); Use a different embedding provider/dimension
- **Because:** text-embedding-3-small is a compact, commonly available embedding model; matching dimensions is important for creating the native vector index. Making it configurable allows users to change provider or dims.
- **Reason came from:** `prompt`
- **Evidence:** Common choice and the code's default: OPENAI_EMBEDDING_MODEL env default 'text-embedding-3-small' and EMBEDDING_DIMENSIONS default '1536' in enrich/enrich.py.
- **When:** 2026-11-25T12:21:23+00:00

## D013 (build): I chose to escape braces in the f-string prompt by doubling them so the JSON appears verbatim in the injected prompt string.

- **Instead of:** Leave the OpenAI prompt as-is and risk syntax error; Escape braces in the f-string to produce literal JSON in the prompt
- **Because:** To produce a valid Python string that contains literal JSON braces in an f-string, braces must be doubled. This is a minimal code change to restore functionality.
- **Reason came from:** `tool_result`
- **Evidence:** enrich/enrich.py raised SyntaxError due to unescaped braces inside an f-string.
- **When:** 2026-11-25T12:21:29+00:00

## D014 (build): I chose to add src/__init__.py to make it an importable package, keeping the simple top-level script entrypoints unchanged.

- **Instead of:** Run scripts with PYTHONPATH set or change imports to relative; Make src a package by adding __init__.py
- **Because:** Adding __init__.py is a minimal change to allow 'from src.db import init_db' to work across scripts and is a common repo layout practice.
- **Reason came from:** `tool_result`
- **Evidence:** ModuleNotFoundError: No module named 'src' when running enrich/enrich.py.
- **When:** 2026-11-25T12:21:44+00:00

## D015 (build): I chose to append the repository root to sys.path at the top of scripts to ensure 'src' imports work when running scripts directly, which is a minimal local-dev convenience change for samples.

- **Instead of:** Modify all scripts to use package install (pip); Temporarily append repo root to sys.path in scripts for simplicity
- **Because:** Keeps scripts runnable directly without requiring users to install the package; acceptable for a sample repo.
- **Reason came from:** `model_default`
- **Evidence:** ModuleNotFoundError persisted after adding src/__init__.py; inserting repo root into sys.path is a standard fix for scripts.
- **When:** 2026-11-25T12:22:01+00:00

## D016 (build): I chose to update src/models.py to use Beanie's current recommended Settings class (set name = 'survey_responses') and remove the deprecated Collection inner class.

- **Instead of:** Keep deprecated Collection inner class and accept Beanie deprecation error; Update models.py to use Settings class per Beanie 1.24 requirements
- **Because:** Fixing the model to current Beanie API ensures init_beanie succeeds and the sample works with the pinned package versions.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime beanie.exceptions.Deprecation: 'Collection inner class is not supported more. Please use Settings instead.'
- **When:** 2026-11-25T12:22:17+00:00

## D017 (build): I chose to call client.close() without await at the end of enrich_all, because AsyncIOMotorClient.close() is synchronous and not awaitable.

- **Instead of:** Call await client.close() for Motor client; Call client.close() without await since AsyncIOMotorClient.close() is synchronous
- **Because:** Calling client.close() synchronously prevents the TypeError and correctly closes sockets.
- **Reason came from:** `tool_result`
- **Evidence:** TypeError: object NoneType can't be used in 'await' expression when attempting to await client.close(). The Motor client close() is synchronous per Motor docs.
- **When:** 2026-11-25T12:22:37+00:00

## D018 (build): I chose to create a vector-diskann index on 'embedding' with dimensions=1536 and similarity='COS' via the documentdb MCP create_index API.

- **Instead of:** Create native vector-diskann index on embedding; Skip creating vector index
- **Because:** Enables efficient vector search matching the sample embedding dims.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill guidance: 'Create a vector-diskann index with correct dimensions, similarity.'
- **When:** 2026-11-25T12:23:32+00:00

## D019 (build): I chose to stop retrying the MCP create_index call after it failed and record the failure; the sample will document the expected vector index and leave manual creation via portal/CLI as fallback.

- **Instead of:** Retry different API payloads until success; Stop and record that MCP create_index failed and require manual portal/CLI index creation
- **Because:** Repeated tool failures indicate either permissions, API mismatch, or server-side restriction; per builder guidance stop after second attempt and take alternate route to avoid causing side effects or infinite retries.
- **Reason came from:** `readiness_report`
- **Evidence:** documentdb_create_index tool returned an error twice with vague 'Function failed' message when attempting to create a vector index.
- **When:** 2026-11-25T12:24:05+00:00
