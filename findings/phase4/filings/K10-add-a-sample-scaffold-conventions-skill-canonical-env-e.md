---
id: K10
title: "Add a sample-scaffold conventions skill: canonical .env.example contract, README checklist and helpers"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 74
member_drafts:
  - 081-agent-kit-sample-scaffold-conventions-complete-env-example-w.md
  - 012-believes-the-connection-string-is-the-legacy-cosmos-db-for-m.md
  - 087-sample-conventions-page-canonical-env-example-env-var-names-.md
open_questions: 2
---

# Add a sample-scaffold conventions skill: canonical `.env.example` contract, README checklist and helpers

## What happens today

The kit explains how to connect, index, seed and search Azure DocumentDB. It gives an agent nothing to copy when it is asked to **build a sample app**:

- The only `.env.example` guidance (`skills/local-deployment/local-env-driven-config.md`) lists two variables. App, seeding, LLM/embedding and MCP variables are left to the model's prior.
- The kit disagrees with itself on the URI variable name: skills use `DOCUMENTDB_URI`; `compat/PROMPT.md`, `compat/QUICKSTART.md`, `scenarios/ecommerce-advanced/README.md` and the code behind them (`compat/src/database.js`, `scenarios/ecommerce-advanced/scripts/load.mjs`) use `MONGODB_URI`.
- No skill names a default chat model, embedding model or embedding dimension, or says that the `cosmosSearch` index `dimensions` should come from configuration rather than a literal.
- No skill says what the connection string is **not**. Agents fall back to the Azure Cosmos DB for MongoDB (RU) shape (`mongodb://`, `.mongo.cosmos.azure.com`, port `10255`, `replicaSet=globaldb`) and commit it as the placeholder.
- No README convention exists for clean-up, "tested with" versions, or recording choices the prompt left open.

Resulting defects seen in generated samples:

- `.env.example` and code disagree: `CHAT_MODEL` templated, `MODEL_NAME` read; `OPENAI_MODEL` vs `OPENAI_CHAT_MODEL`; `DB_NAME`, `PORT`, `SEED_COUNT` read but never templated. Filling in the template silently does nothing.
- `EMBEDDING_DIM=384` in `.env.example`, `1536` in the seed script; `dimensions: 1536` hard-coded in `createIndexes`, so changing the model breaks the index.
- Placeholders such as `...@<cluster>.mongocluster.cosmos.azure.com:10260/?tls=true&replicaSet=globaldb` (an RU/vCore hybrid).
- Seeding embedded in a demo script, not re-runnable, with no tag a clean-up can target.
- `ENABLE_MANAGEMENT_TOOLS` missing after the MCP server refused `create_index`.

## Why it matters

In one experiment run (100 sample prompts, gpt-5-mini, this kit plus the DocumentDB, Azure and Learn MCP servers), **74 distinct samples** produced at least one audit or readiness finding traced to this gap (128 findings). About 26 samples committed an RU-shaped or hybrid connection placeholder, and builders logged their model, dimension and env-name choices as `model_default` with nothing to cite. Part of the count comes from cold-quiz answers, which measure model priors rather than shipped code. The counts are from this single run and should not be quoted externally without a re-run.

These files are what a developer copies. A template that disagrees with the code, an index whose `dimensions` do not match the stored vectors, or a seed with no clean-up gives a sample that runs for its author and fails for the next reader.

## Proposed change

One new standalone skill, `skills/sample-scaffold/` (`name: documentdb-sample-scaffold`; a standalone `SKILL.md` skill like `mcp-setup/`, plus supporting files), and one-line wiring. Parts of the member drafts land in sibling PRs and are linked, not repeated, here:

- `retryWrites` value and the `.documentdb.azure.com` host-suffix corrections in existing skills, including the cloud placeholder in `local-env-driven-config.md`: K01.
- Detailed bulk-load guidance (`ordered=False` / `bulkWrite`, `--force` wipe-and-reseed, printed counts): K08.
- Index verification from code (`ensure_indexes`, no `COLLSCAN`, index the fields you `$match` / `$group` on): K06, with the `explain("executionStats")` script in K33.
- Change-stream resume-token checkpointing: K04.
- Client retries for transient database errors: K07. Beanie client setup: K37. Dependency pinning and the tested-stack matrix: K29.

### 1. `skills/sample-scaffold/SKILL.md`

Description: "Conventions for generating a runnable Azure DocumentDB sample: complete `.env.example`, canonical variable names, README checklist, singleton client helpers, a re-runnable seed, and LLM/embedding defaults with `EMBEDDING_DIMS` driving the `cosmosSearch` index. Use when building, scaffolding or reviewing a sample, demo or quickstart."

Body: a "Before you publish" checklist linking to the files below, and the core rule: **every variable the code reads appears in `.env.example` with a comment, and every key in `.env.example` is read somewhere.**

### 2. `skills/sample-scaffold/env.example` (samples copy it to `.env.example`)

```dotenv
# ---- Azure DocumentDB (required) ----
# Copy from portal -> cluster -> Settings -> Connection strings, `az documentdb mongocluster list-connection-strings`
# (pick the entry by name: it lists GlobalReadWrite first and Self second),
# or `az documentdb mongocluster show --query properties.connectionString` (the default Self string). Never build the host from the cluster name.
# The portal offers two strings. On a single cluster the Self string (<cluster>.mongocluster.cosmos.azure.com) and the
# Global read-write string (<cluster>.global.mongocluster.cosmos.azure.com) are interchangeable. If the cluster has or may
# get a cross-region replica, use the Global read-write string for writes; the old primary's Self string turns read-only after a promotion.
# Keep retrywrites=false: Azure DocumentDB does not support retryable writes (the server does not de-duplicate a retried write).
DOCUMENTDB_URI=mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
DATABASE_NAME=sample_app
# Local gateway container only; never true against a managed cluster
# DOCUMENTDB_ALLOW_INVALID_CERTS=true

# ---- App (optional, defaults shown) ----
PORT=3000
LOG_LEVEL=info
MAX_POOL_SIZE=50
SEED_VERSION=1
SEED_COUNT=100

# ---- LLM / embeddings (AI samples only) ----
# stub | openai | azure-openai. stub = deterministic, no key, used by tests/CI.
LLM_PROVIDER=stub
OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=2024-10-21
# Example defaults; for azure-openai these hold deployment names
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
# Must equal the model's output size; the vector index is created from it.
# Limits: 2,000 dimensions; 4,000 with compression "half" (HNSW, IVF); 16,000 with product quantization (DiskANN)
EMBEDDING_DIMS=1536
# vector-diskann | vector-hnsw | vector-ivf
VECTOR_INDEX_KIND=vector-hnsw
VECTOR_SIMILARITY=COS

# ---- DocumentDB MCP server (agent-driven dev/CI only) ----
# true lets an agent write data and create/drop indexes; scope to a throwaway cluster
ENABLE_WRITE_TOOLS=false
ENABLE_MANAGEMENT_TOOLS=false
```

### 3. `skills/sample-scaffold/sample-env-contract.md`

- Names in `env.example` are canonical; no `MODEL`, `MODEL_NAME`, `OPENAI_MODEL`, `EMBEDDING_DIM`, `DB_NAME`, `MONGODB_URI` drift.
- Placeholders only; `.env` gitignored, `.env.example` committed; secrets never stored in documents.
- **Connection placeholder rule:** use the shape above. Never write a cloud `mongodb://` URI with a port, `replicaSet=globaldb`, an account key, or a `.mongo.cosmos.azure.com` / `.documents.azure.com` host; those belong to Azure Cosmos DB RU-based accounts, a different service. A `mongodb://` string with an Azure DocumentDB cluster host does not resolve either: the cluster hosts are SRV names with no A record (managed test, 2026-11-25). The only Azure DocumentDB hosts are `<cluster>.mongocluster.cosmos.azure.com` (portal label "Self (always this cluster)") and `<cluster>.global.mongocluster.cosmos.azure.com` ("Global read-write"); a `.mongocluster.documentdb.azure.com` suffix does not exist. Copy the string the portal, CLI or REST API returns and never construct the host from the cluster name (Learn Mongoose tutorial, "Verify the cluster from a terminal"). Prefer `tls=true` over the legacy `ssl=true` alias. `localhost:10260` is the local gateway only.
- **Self vs Global read-write rule:** on a single cluster either string works ("you can use either connection string indiscriminately", Learn RBAC page). If the cluster has or may get a cross-region replica, use the Global read-write string for writes so a promotion needs no code change; the former primary's Self string becomes read-only after promotion, and replica clusters expose only a Self string. Reads may use either. In-region HA failover changes neither string. Sources: Learn how-to-connect-role-based-access-control ("Get cluster credentials"), how-to-cluster-replica ("Use connection strings"), how-to-private-link (replica note), availability-disaster-recovery-under-hood (summary table footnote); decision in findings/phase4/DECISIONS.md (host forms).
- **retryWrites rule:** Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys). Helpers and samples never set `retryWrites: true` in client options (see documentdb/documentdb#767; decision in findings/phase4/DECISIONS.md).
- Optional lint for a sample's test script:
  ```bash
  diff <(grep -rhoE 'process\.env\.[A-Z0-9_]+|os\.(getenv|environ(\.get)?)\(["'"'"'][A-Z0-9_]+' src scripts | grep -oE '[A-Z][A-Z0-9_]+' | sort -u) <(grep -oE '^#? ?[A-Z][A-Z0-9_]+=' .env.example | tr -d '# =' | sort -u)
  ```

### 4. `skills/sample-scaffold/sample-readme-checklist.md`

README sections in order: Prerequisites; Configuration (a table of every variable from `.env.example`); Run; Seed (`npm run seed` / `python -m app.seed`); Verify (expected output, `explain()` check per the indexing skill); **Clean up** (drop the sample database or `deleteMany({ seeded: true })`, drop named indexes, remove local containers); **Tested with** (runtime, driver, framework versions, cluster tier, date); **Defaults used** (one row per value the prompt left open or any substitution made, for example an ODM swapped for the runtime-native one: choice, value, one-line reason); Install notes (pinned lockfile or `requirements.txt`, and a known-workaround hint such as `pip install --only-binary=:all: pydantic-core` when a native build is known to fail; pinning rules per K29).

### 5. `skills/sample-scaffold/sample-db-helper.md` (+ `templates/db.py`, `templates/db.js`)

Module-level `get_client()` / `get_db()` singletons that read `DOCUMENTDB_URI` and `DATABASE_NAME`, exit with a clear message when unset, apply `MAX_POOL_SIZE` from env, honor `DOCUMENTDB_ALLOW_INVALID_CERTS` only when explicitly `true`, do not override the options carried by the copied connection string, and export exactly the names other scripts import. The Python page shows, for Beanie samples, one `init_beanie(database=get_db(), document_models=[...])` call at startup (client type per K37) with explicit field types (`list[float]` for vectors, `float` for scores). Seed scripts are standalone, create collections and indexes through the driver first (an HNSW vector index can be created on an empty collection; an IVF index, whose `numLists` depends on the document count, and a product-quantization index are created after the data is loaded; Learn says a new vector index can return empty results for 2 to 3 minutes while it builds, which the managed test did not see on 5-document collections), upsert on a deterministic key, tag documents `seeded: true, seed_version`, are safe to re-run, and print counts; `--force` wipes and reseeds (bulk-write details in K08). An identical `createIndexes` (same name, same options in the same key order, defaults included) is a no-op; the same name with other options fails with 86 `IndexKeySpecsConflict`, and a second vector index on a path with 85 `IndexOptionsConflict` (managed service and documentdb-local; undocumented on Learn). So the ensure-index step sends a fixed, fully explicit spec, or compares against `listIndexes` before creating, and surfaces 85 and 86 (helper in K06).

### 6. `skills/sample-scaffold/sample-ai-conventions.md`

- Defaults: `LLM_PROVIDER=stub` for tests; `openai` with `CHAT_MODEL` / `EMBEDDING_MODEL` / `EMBEDDING_DIMS` for live calls; `azure-openai` reuses the same two model variables as deployment names. These are sample defaults, not a service recommendation. When the chat model is retired, only `CHAT_MODEL` changes; the vector index depends only on `EMBEDDING_MODEL` / `EMBEDDING_DIMS`.
- Stacks and dimensions: OpenAI or Azure OpenAI `text-embedding-3-small` -> 1536; for image prompts a local image model (for example CLIP ViT-B/32 -> 512) with `EMBEDDING_DIMS` set to match.
- One `get_embedder()` / `get_chat()` factory switching on `LLM_PROVIDER`.
- Create the `cosmosSearch` index from `EMBEDDING_DIMS`, never a literal, and keep `EMBEDDING_DIMS` within the documented limits: 2,000 dimensions; 4,000 with `compression: "half"` on HNSW or IVF; 16,000 with product quantization on DiskANN. Store vectors as a plain array of numbers (`number[]` / `list[float]`) and have the skill name BSON binary explicitly: a BSON binary vector is stored but not indexed and is silently absent from results, and a binary query vector is rejected (`expected an array type field`). One vector index per vector path:
  ```javascript
  const dims = Number(process.env.EMBEDDING_DIMS ?? 1536);
  await db.command({ createIndexes: 'docs', indexes: [{ name: 'embedding_idx',
    key: { embedding: 'cosmosSearch' },
    cosmosSearchOptions: { kind: process.env.VECTOR_INDEX_KIND ?? 'vector-hnsw',
      similarity: process.env.VECTOR_SIMILARITY ?? 'COS', dimensions: dims } }] });
  ```
  Add the kind-specific build options from the vector-search skill, quoting the documented ranges and defaults; for the default `vector-hnsw`: `m` 2 to 100 (default 16), `efConstruction` 4 to 1000 and at least `2m` (default 64), `efSearch` default 40 at query time. `listIndexes` reports these options under `cosmosSearchOptions` (the Learn sample showing `cosmosSearch` is wrong), which the Verify step can check. Send the same spec on every run, in a fixed key order and with every value explicit: a repeat is a no-op only when the options are identical, and the same name with other options fails with 86.
- Before creating the index, embed one probe string and assert its length equals `EMBEDDING_DIMS`.
- Stub mode: `embed()` returns a deterministic, L2-normalized `number[]` of length `EMBEDDING_DIMS` (not semantic); `chat()` returns a canned, schema-valid reply. Tests run with the stub; a `test:live` script sets `LLM_PROVIDER=openai` and is skipped when no key is set.
- Keys: read from env only, never logged, echoed or stored with prompts. When a sample exposes LLM calls over HTTP, add a simple per-process rate limiter. Model-provider calls get exponential backoff on the provider's HTTP 429/5xx and bounded concurrency, both overridable by env (two lines). This is the model provider's rate limit, not a database signal: Azure DocumentDB returns no 429 or 16500 throttling code, so database retry logic must not key on those (database retries are K07).
- Embedder outage: persist `embedding: null, needs_embedding: true`, index `{ needs_embedding: 1 }`, ship a `backfill` script. Store `embeddingModel` / `embeddingDims` per document as in `vector-normalize-embeddings.md`.
- LLM write-back: audit fields `{ model_id, prompt_hash, generated_at, agent_names[], deterministic_score, llm_score, raw_output_ref }` applied with one atomic `$set`.
- Agent memory: persist identifiers (`conversation_id`, `last_entity_id`) and resolved time ranges as BSON dates, not free text, so they can be indexed and range-queried; model a workflow run as one document per run with `status` and `resume_from`, indexed on `{ status: 1, updated_at: 1 }`. Monitors and trackers keep a per-entity current-state collection with a unique id (link `data-modeling`).
- ODM substitution: if the prompt names an ODM from another runtime (Beanie for a Node sample), use the runtime-native one (Mongoose) and record it under "Defaults used".

### 7. Edits to existing files

- `skills/connection/SKILL.md`, under "Connection String Format", add: "**Not Cosmos DB for MongoDB (RU).** Azure DocumentDB publishes `mongodb+srv://` strings on `<cluster>.mongocluster.cosmos.azure.com` (Self) and `<cluster>.global.mongocluster.cosmos.azure.com` (Global read-write), so no port appears. On a single cluster the two are interchangeable; if the cluster has or may get a cross-region replica, use the Global read-write string for writes, since the old primary's Self string becomes read-only after promotion. `replicaSet=globaldb`, port `10255` and `.mongo.cosmos.azure.com` hosts belong to RU-based accounts. Copy the string from the portal, CLI or REST API; never construct the host from the cluster name." (Sources: Learn how-to-connect-role-based-access-control, how-to-cluster-replica, tutorial-nodejs-mongoose.)
- `skills/azure-deployment/SKILL.md` (line 288 shows the `.global.` form as "Form of the connection string" with no explanation, while `skills/connection/SKILL.md`, `skills/mcp-setup/SKILL.md`, `README.md`, `GEMINI.md`, `install.sh`, `install.ps1` and `docs/installation/macos.md` show the plain form): switch it to the plain form and add the same one-line Self/Global note, so every kit snippet agrees.
- `compat/PROMPT.md`, `compat/QUICKSTART.md`, `scenarios/ecommerce-advanced/README.md`, `compat/src/database.js`, `scenarios/ecommerce-advanced/scripts/load.mjs`: `MONGODB_URI` -> `DOCUMENTDB_URI` (optionally read the old name as a fallback for one release).
- One-line pointers to `documentdb-sample-scaffold` in `local-deployment/SKILL.md`, `local-env-driven-config.md`, `connection/SKILL.md`, `driver/SKILL.md`, `vector-search/SKILL.md` and `mcp-setup/SKILL.md`.
- New row in the `AGENTS.md` "Interactive / workflow skills" table, a line under "Routing hints for agents" ("Building or scaffolding a sample app" -> `documentdb-sample-scaffold`), a row in the `docs/SKILLS.md` "Standalone SKILL.md skills" table, and a `CHANGELOG.md` entry.

Out of scope: generic framework choices (Python minor, web framework, scheduler); samples only record them under "Defaults used".

## Evidence

Run folders in the experiment repository (`runs/`):

- `runs/14-customer-complaint-classifier/20261124-201931/`: `.env.example` names differ from those read in `src/app/pipeline.py`
- `runs/04-regulatory-reporting-orchestration/20261124-200545/`: `CHAT_MODEL` templated, `MODEL_NAME` read in `app/src/agents.py`
- `runs/14-hyper-personalized-content-engine/20261124-205043/`: `EMBEDDING_DIM=384` vs a 1536 default in `app/scripts/seed.js`
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/`: RU-shaped placeholder in `.env.example`
- `runs/18-sanctions-list-screening-agent/20261124-202645/`: `dimensions` hard-coded in index creation (`05-audit.json`)
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/`: MCP management-tools refusal in `events.jsonl`; flag absent from `.env.example`

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Vector-index facts: settled 2026-11-25 from the Learn vector-search, half-precision, product-quantization and limitations pages and engine issue documentdb/documentdb#109, see findings/phase4/DECISIONS.md.
  - HNSW build options are quoted as the documented ranges and defaults: `m` 2 to 100 (default 16), `efConstruction` 4 to 1000 and at least `2m` (default 64), `efSearch` default 40 (vector-search page, HNSW tab).
  - `EMBEDDING_DIMS` limits: 2,000; 4,000 with `compression: "half"` on HNSW or IVF; 16,000 with product quantization on DiskANN (vector-search "Features and limitations", half-precision, product-quantization and limitations pages).
  - Vectors are stored as a plain array of numbers: a BSON binary vector is stored but not indexed and a binary query vector is rejected (vector-search DiskANN field table and IVF Important box; documentdb/documentdb#109).
  - Build order for seed scripts: HNSW on an empty collection; IVF and product quantization after loading; Learn's empty results for 2 to 3 minutes while a new index builds (vector-search HNSW column; product-quantization page note; quickstart-nodejs-select-algorithm Troubleshooting) did not occur on 5-document collections in the managed test of 2026-11-25 (large collections untested).
  - `listIndexes` reports vector options under `cosmosSearchOptions` only, on the managed service and documentdb-local; the Learn sample (vector-search, "Get vector index definitions") that shows `cosmosSearch` is wrong (ENGINE-TESTS.md, Managed service; DECISIONS.md topic 6).
  - Same-name index behaviour is undocumented on Learn and not an SME item, now observed on the managed service: an identical repeat is a no-op only when the options are identical, key order and defaults included; other options under the same name fail with 86, a second vector index on a path with 85 (DECISIONS.md topic 6, "Not an SME item, now observed").
- Global read-write host: settled 2026-11-25 from Learn, no SME needed (DECISIONS.md, "Host forms"). The `.global.` host is never required; it is the Global read-write string the portal offers on the primary cluster beside the Self string, on a single cluster the two are interchangeable, and a cluster that has or may get a cross-region replica should use the Global read-write string for writes because the old primary's Self string becomes read-only after promotion; the host is copied from the portal, CLI or REST API, never constructed from the cluster name. The template now carries that comment and the plain (Self) host as its default. The managed test of 2026-11-25 observed the `.global.` host resolving, authenticating and taking writes on a single cluster with no replica, and `list-connection-strings` returning `GlobalReadWrite` first and `Self` second (ENGINE-TESTS.md, Managed service). Sources: Learn how-to-connect-role-based-access-control ("Get cluster credentials"), how-to-cluster-replica ("Use connection strings"), cross-region-replication, availability-disaster-recovery-under-hood (summary table footnote), how-to-private-link (replica note), tutorial-nodejs-mongoose ("Verify the cluster from a terminal"). What error a client on the Global string sees during a promotion is still open for engineering (DECISIONS.md, topics 2 and 3) and does not affect this template.

## Open questions

1. **Default models.** Are `gpt-4o-mini` and `text-embedding-3-small` / 1536 acceptable sample defaults for the kit, or should the kit name none and require `CHAT_MODEL` / `EMBEDDING_MODEL` to be set? Maintainer decision.
2. **Variable names.** The drafts proposed `DATABASE_NAME` vs `DB_NAME`, `LLM_PROVIDER` vs `MODEL_PROVIDER`, and separate `AZURE_OPENAI_CHAT_DEPLOYMENT` / `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` vs reusing `CHAT_MODEL` / `EMBEDDING_MODEL` as deployment names. This PR picks `DATABASE_NAME`, `LLM_PROVIDER` and the reuse. Sibling PRs currently use other database-name variables (`DOCUMENTDB_DATABASE` in K07, `DB_NAME` in K08, K09 and K37); one name must be chosen and applied across all of them before filing. Do maintainers prefer otherwise?

## Source drafts

- 081-agent-kit-sample-scaffold-conventions-complete-env-example-w.md
- 012-believes-the-connection-string-is-the-legacy-cosmos-db-for-m.md
- 087-sample-conventions-page-canonical-env-example-env-var-names-.md
