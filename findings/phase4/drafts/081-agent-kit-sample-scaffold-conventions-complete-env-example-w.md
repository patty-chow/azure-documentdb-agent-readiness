---
title: "Add a documentdb-sample-scaffold skill: complete .env.example, README checklist, db/seed/verify helpers, AI-sample conventions (and fix retryWrites=true in connection/driver skills)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 32
findings: 53
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a `documentdb-sample-scaffold` skill: complete `.env.example`, README checklist, db/seed/verify helpers, AI-sample conventions (and fix retryWrites=true in connection/driver skills)

## What happens today

The kit explains *how* to connect, index, seed and search, but gives an agent nothing to copy when it is asked to **build a sample app**. `local-env-driven-config.md` shows a two-line `.env.example`, `driver-singleton-client.md` shows a 6-line Node singleton, `local-sample-data-management.md` covers mongosh `INIT_DATA_PATH` scripts for the local image only, and the MCP opt-in flags live in `README.md` / `mcp-setup/SKILL.md` where a sample author never looks. Every other scaffold decision (which env-var names, which embedding model and dimension, how to seed, how to clean up, what to pin) is left to the model's prior.

We ran a five-stage readiness pipeline (prompt review, cold quiz, build, decision log, audit) over 100 Azure DocumentDB sample prompts with gpt-5-mini using this kit plus the DocumentDB/Azure/Learn MCP servers. 53 audit findings across **32 of the 100 samples** are the same scaffold defect in different clothes. A scan of all 117 run folders (101 distinct samples) confirms the pattern is not limited to those 32:

| Defect | Run folders affected |
|---|---|
| `.env.example` present but omits a variable the code reads (`PORT`, `DB_NAME`/`DATABASE_NAME`, `MAX_POOL_SIZE`, `EMBEDDING_MODEL`, `EMBEDDING_DIMS`, `LLM_MODEL`, `TWILIO_FROM_NUMBER`, `SEED_COUNT`, …) | 44 |
| No `.env.example` at all | 6 |
| README has no Clean-up / teardown section | 29 |
| README has no "tested with" matrix | 90 |
| Build decisions about LLM / embedding model / dims / env names logged with `reason_source=model_default` and nothing to cite | 91 |
| MCP `create_index` call failed with "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in." | 36 |

Concrete examples from the run folders:

- `14-customer-complaint-classifier`: `.env.example` lists `DOCUMENTDB_URI`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, `DOCUMENTDB_DB_NAME`; the code reads `DATABASE_NAME`, `COLLECTION_NAME`, `EMBEDDING_MODEL`, `LLM_MODEL` instead. A user copying the example gets a different database name than the one the code uses.
- `04-regulatory-reporting-orchestration`: `.env.example` says `CHAT_MODEL=gpt-4o-mini`; `src/agents.py` reads `os.environ.get("MODEL_NAME", ...)`. Filling in `CHAT_MODEL` does nothing.
- `14-hyper-personalized-content-engine`: `.env.example` says `EMBEDDING_DIM=384`, `src/server.js` and `src/seed.js` default to 384, `scripts/seed.js` defaults to 1536. The audit records index-creation attempts with inconsistent `dimensions`.
- `11-visual-similarity-search-image-embeddings`: builder tried MCP `create_index`, got the opt-in error, and the shipped `.env.example` still lists only `DOCUMENTDB_URI` (no `HF_TOKEN`, no `ENABLE_MANAGEMENT_TOOLS`).
- `05-kyc-document-ingestion-pipeline`: seed script re-run creates duplicates (two records have no deterministic key); no idempotent index-init script; `.env.example` lacks `DB_NAME`.
- `07-customer-review-sentiment-pipeline`: `create_indexes.py` and `aggregations.py` import a `get_motor_client` helper that `db.py` did not export; `$group` on `sentiment_label` while the index was built on `sentiment_score`, never checked with `explain()`.
- `11-market-news-sentiment-orchestration`, `11-correspondent-banking-risk-screener`: seeding lives inside `demo.js` with no `npm run seed`; seeded documents carry no `seeded`/`seed_version` tag so no clean-up can target them.

## Why it matters

These are the artifacts a developer actually copies. A `.env.example` that disagrees with the code, an index whose `dimensions` does not match the stored vectors (which must be `number[]` to be indexed by `cosmosSearch`), and a seed with no clean-up all produce a sample that "works on the builder's machine" and fails or litters the cluster for the next person. Because the kit is silent, every build re-derives these conventions from model memory, so 100 samples ship 100 slightly different scaffolds and the audit cannot cite a source for any of them.

## Proposed change

Add one standalone skill, `skills/sample-scaffold/` (`name: documentdb-sample-scaffold`, same shape as `mcp-setup/` and `azure-deployment/`), and wire it in with one-line cross-references. Nothing existing is rewritten.

### 1. `skills/sample-scaffold/SKILL.md`

Front matter `description`: "Scaffold conventions for Azure DocumentDB sample apps — complete `.env.example`, README checklist, singleton `get_client()` helpers, idempotent seed/init script, `explain()` index verification, change-stream checkpointing, and LLM/embedding defaults for AI-augmented samples. Use when generating, reviewing or publishing a sample or quickstart app."

Body: a 7-item "Before you publish a sample" checklist linking to the rule files below, plus the rule: **every environment variable the code reads must appear in `.env.example` with a comment; every `.env.example` key must be read somewhere** (agents can verify this with a grep in both directions).

### 2. `scaffold-env-example.md` + `templates/.env.example`

Canonical names (one table: name, required/optional, default, one-line purpose). Template:

```dotenv
# ---- Azure DocumentDB (required) ----
# Copy from the cluster's Connection strings pane. Keep retrywrites=false.
DOCUMENTDB_URI=mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
DATABASE_NAME=sample_<domain>_<nn>
# Local Gateway container only — never true against a managed cluster
DOCUMENTDB_ALLOW_INVALID_CERTS=false

# ---- App (optional, defaults shown) ----
PORT=3000
LOG_LEVEL=info
MAX_POOL_SIZE=50
MAX_IDLE_TIME_MS=120000

# ---- Seeding (optional) ----
SEED_VERSION=1
SEED_COUNT=100

# ---- LLM / embeddings (only for AI-augmented samples) ----
MODEL_PROVIDER=openai            # openai | azure-openai | demo
OPENAI_API_KEY=
# Example default only; use any chat model/deployment available to you
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMS=1536              # MUST equal the model's output size and the index 'dimensions'
# Azure OpenAI variant (set MODEL_PROVIDER=azure-openai)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=
# Run without any model key: deterministic hash-based vectors of EMBEDDING_DIMS (demo only, not semantic)
USE_DEMO_EMBEDDINGS=false

# ---- DocumentDB MCP server (only when an agent runs management ops in CI/dev) ----
# Both default to false. true lets the agent insert/update/delete and create/drop indexes
# and databases through MCP — scope to a throwaway cluster.
ENABLE_WRITE_TOOLS=false
ENABLE_MANAGEMENT_TOOLS=false
```

Rules in the page: names above are canonical (no `MODEL`, `MODEL_NAME`, `OPENAI_MODEL`, `EMBEDDING_DIM`, `DB_NAME` drift); placeholders only, never real values; secrets go in env / Key Vault, never in documents (`1938` finding); `.env` is gitignored, `.env.example` is committed.

### 3. `scaffold-readme-checklist.md`

Required README sections, in order: Prerequisites · Configuration (**table of every env var**, generated from `.env.example`) · Run · Seed (`npm run seed` / `python -m app.seed`) · Verify (what to run, expected output, `explain()` check) · **Clean up** (drop the sample database or `deleteMany({seeded: true})`, drop the vector/text indexes by name, remove any local container/volume) · **Tested with** (runtime, driver, ODM, framework versions, cluster tier and server version, date) · Install notes (pinned `requirements.txt`/lockfile; `pip install --only-binary=:all: pydantic-core` style hints when a native build is known to fail) · Decisions (any substitution, e.g. ODM swapped because the prompt named one from another runtime).

### 4. `scaffold-db-helper.md` (+ `templates/db.py`, `templates/db.js`)

Module-level `get_client()` / `get_db()` singletons that: read `DOCUMENTDB_URI` and `DATABASE_NAME`, exit with a clear message when unset, apply `maxPoolSize`/`maxIdleTimeMS` from env, honor `DOCUMENTDB_ALLOW_INVALID_CERTS` only when explicitly `true`, do **not** pass `retryWrites: true` (the canonical Azure DocumentDB connection string carries `retrywrites=false`; note that the kit itself currently shows `retryWrites=true` in two places, fixed in section 9), and export exactly the names the other scripts import. Python variant shows `init_beanie(database=get_db(), document_models=[...])` once at startup for Beanie samples, with explicit field types (`list[float]` for vectors, `float` for scores).

### 5. `scaffold-seed-and-init.md` (+ `templates/seed_and_init.{py,js}`)

Standalone script, never inside a demo: creates collections and declared indexes first (via the driver, not via MCP), then bulk-upserts seed documents keyed on a deterministic `_id` or natural key, tags each with `seeded: true, seed_version: <SEED_VERSION>`, uses `insert_many(ordered=False)` / `bulkWrite` for volume, is safe to re-run, supports `--force` to wipe-and-reseed, and prints counts. Pairs with the Clean-up section (`deleteMany({seeded: true})`). Note that `local-sample-data-management.md` covers the local image's `INIT_DATA_PATH` path; this script is the cross-environment path `local-prod-parity.md` asks for.

### 6. `scaffold-verify-indexes.md` (+ `templates/verify_indexes.{py,js}`)

Runs each of the sample's critical queries and aggregations through `explain("executionStats")`, prints `totalKeysExamined` / `totalDocsExamined` / `executionTimeMillis` and fails if a `COLLSCAN` appears. Includes the group-by rule the `07` run violated: *index the field you `$match` and `$group` on, not the field you aggregate* (`{product_id: 1, sentiment_label: 1}` for a per-product label count).

### 7. `scaffold-ai-sample-conventions.md`

For AI-augmented samples, fixes what the builders currently invent:

- **Recommended stacks and dims**: OpenAI `text-embedding-3-small` → 1536; Azure OpenAI deployment of the same → 1536; `USE_DEMO_EMBEDDINGS` deterministic hash vectors at `EMBEDDING_DIMS` (state plainly: not semantic, demo only); local image models (e.g. CLIP ViT-B/32 → 512) when the prompt is about images. Chat model is read from `CHAT_MODEL`; the template value is an example, not a recommendation tied to the service.
- **Dims-match check**: before `createIndexes`, embed one probe string and assert `len(vector) == EMBEDDING_DIMS`; store `embedding_model` and `embedding_dims` on each document (already in `vector-normalize-embeddings.md`; link it). Vectors must be plain `number[]`.
- **Provider-agnostic wiring**: one `get_embedder()` / `get_chat()` factory switching on `MODEL_PROVIDER`.
- **Retries and concurrency**: exponential backoff on model-provider 429/5xx and a bounded LLM concurrency, both overridable by env (keep this to two lines; it is model-provider hygiene, not DocumentDB guidance).
- **Write-back schema for audit fields**: `{ model_id, prompt_hash, generated_at, agent_names[], deterministic_score, llm_score, raw_output_ref }` applied with atomic `$set`.
- **Agent memory**: persist identifiers (`conversation_id`, `last_entity_id`) and resolved time ranges as BSON dates (not free text) so they can be indexed and range-queried; model workflow runs as one document per run with `status` and `resume_from`, indexed on `{status: 1, updated_at: 1}`.
- **Per-entity current-state** collections with a unique id for monitors/trackers (link `data-modeling`).
- **ODM substitution rule**: if the prompt names an ODM from another runtime (Beanie for Node), use the runtime-native equivalent (Mongoose) and record it under Decisions.

### 8. `scaffold-change-stream-checkpoint.md` (+ template)

Persist the resume token to a `change_stream_checkpoints` collection after each processed event, `watch(resumeAfter=token)` on start, handle resumable errors; note the Learn caveats: resume tokens survive failover but the cursor must be reopened, single-shard to multishard topology changes break resumability, and multishard change streams are a preview feature enabled under cluster **Features** (not compatible with the multishard Rebalancer) — link https://learn.microsoft.com/en-us/azure/documentdb/change-streams.

### 9. Cross-references (one line each)

- `skills/local-deployment/SKILL.md` and `local-env-driven-config.md`: "For a complete sample `.env.example`, see `documentdb-sample-scaffold`."
- `skills/connection/SKILL.md` (Singleton Client Pattern) and `skills/driver/SKILL.md`: "Copyable `db.py` / `db.js` helpers live in `documentdb-sample-scaffold`."
- `skills/indexing/SKILL.md`: "Verify a sample's indexes with the `verify_indexes` script in `documentdb-sample-scaffold`."
- `skills/vector-search/SKILL.md`: "Default models/dims and the dims-match check for samples: `documentdb-sample-scaffold`."
- `skills/mcp-setup/SKILL.md` (Notes): "Sample `.env.example` files should list `ENABLE_WRITE_TOOLS` / `ENABLE_MANAGEMENT_TOOLS` as `false` with the trade-off comment — see `documentdb-sample-scaffold`."
- **Fix existing `retryWrites=true`**: `skills/connection/SKILL.md` (Connection String Format, line ~60) shows `...&retryWrites=true`, and `skills/driver/driver-singleton-client.md` passes `{ maxPoolSize: 50, retryWrites: true }`. Change both to the canonical `retrywrites=false&maxIdleTimeMS=120000` form so the new templates and existing skills agree.
- `AGENTS.md` "Skills in this kit" table and `docs/SKILLS.md` standalone-skill table: new row.
- `CHANGELOG.md` entry.

Also fix: `skills/local-deployment/local-env-driven-config.md` (line ~68) and `skills/security/security-entra-rbac.md` (line ~15) show the managed-cluster host as `<cluster>.mongocluster.documentdb.azure.com`; the portal and Learn quickstarts use `<cluster>.mongocluster.cosmos.azure.com`. Align them with `README.md` and the new template, and add the missing `retrywrites=false&maxIdleTimeMS=120000` to the line-68 example.

Out of scope here: the experiment's own build prompt should load this skill before scaffolding; that is a harness change, not a kit change.

## Evidence (run folders under `azure-documentdb-agent-readiness/runs/`)

- `runs/14-customer-complaint-classifier/20261124-201931/` — `app/.env.example` vs `src/app/pipeline.py`, `src/app/db.py`; `doc-gaps.md` "Missing env vars in .env.example"
- `runs/04-regulatory-reporting-orchestration/20261124-200545/` — `app/.env.example` line 11 (`CHAT_MODEL`) vs `app/src/agents.py` line 10 (`MODEL_NAME`); `doc-gaps.md`
- `runs/14-hyper-personalized-content-engine/20261124-205043/` — `app/.env.example` (`EMBEDDING_DIM=384`) vs `app/scripts/seed.js` (1536 default); `doc-gaps.md` "[high] Embedding & chat model defaults and dimensionality"
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/` — `events.jsonl` MCP opt-in error; `doc-gaps.md` ".env.example completeness", "MCP management-tools opt-in"
- `runs/05-kyc-document-ingestion-pipeline/20261124-190500/` — `doc-gaps.md` "Complete .env.example", "Idempotent seed and index-creation script"; also `runs/07-customer-review-sentiment-pipeline/20261125-054042/doc-gaps.md` (missing `get_motor_client`, index/aggregation mismatch)

## Verification

### 1. Already covered? partially_covered
The kit has fragments but no scaffold an agent building a sample can copy:
- `skills/local-deployment/local-env-driven-config.md` shows a two-line `.env.example` (`DOCUMENTDB_URI`, `DOCUMENTDB_ALLOW_INVALID_CERTS`) and a `get_client()` that exits when the URI is unset. No app, seeding, LLM/embedding or MCP variables.
- `skills/driver/driver-singleton-client.md` has a Node module-level singleton only.
- `skills/local-deployment/local-sample-data-management.md` covers `SKIP_INIT_DATA` / `INIT_DATA_PATH` for the local image, not an idempotent, tagged, cross-environment seed script.
- `skills/vector-search/vector-normalize-embeddings.md` line 12: "Store the **embedding model name** and **dimensions** alongside the vector". Partly covers the dims-tracking point, with no dims-match check before index creation.
- `ENABLE_WRITE_TOOLS` / `ENABLE_MANAGEMENT_TOOLS` appear in `README.md` lines 168-169, `GEMINI.md`, `mcp.json` and `skills/mcp-setup/SKILL.md` lines 154-155. They do not appear in any sample or `.env.example` guidance.
- A grep of `skills/` and `knowledge-base/` finds no README checklist, Clean-up, tested-with, `explain()` verify script, or change-stream checkpoint guidance (`grep -rni "scaffold|resumeAfter|change stream"` returns nothing).
- Learn does not cover this either: https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs hard-codes the connection string with no env template, and its "Clean up resources" section only deletes the resource group. https://learn.microsoft.com/en-us/azure/documentdb/change-streams does show resume-token persistence, so the checkpoint template should link to it.

### 2. Premise true? confirmed (with corrections applied)
- The MCP opt-in error text is real. `documentdb-mcp/src/security/authorization.ts` line 50 reads: "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in."
- The canonical connection string uses `retrywrites=false&maxIdleTimeMS=120000`, as in the Learn Node.js quickstart. The draft's db-helper rule is correct. The kit itself contradicts it in `skills/connection/SKILL.md` line 60 (`retryWrites=true`) and `skills/driver/driver-singleton-client.md` (`retryWrites: true`), so I added fixing both to section 9.
- The managed host is `<cluster>.mongocluster.cosmos.azure.com`. The `...mongocluster.documentdb.azure.com` host in `local-env-driven-config.md` and `security-entra-rbac.md` is inconsistent with Learn and the kit README. I turned the draft's side note into a concrete fix.
- Vector facts hold: `text-embedding-3-small` produces 1536 dimensions and CLIP ViT-B/32 produces 512. Vectors must be `number[]` for `cosmosSearch` indexing.
- Change streams: the draft's "multishard prerequisite" was vague. Learn says multishard change streams are a preview enabled under **Features**, cannot run while the multishard Rebalancer is on, and lose resumability on a single-shard to multishard topology change. Cursors must be reopened after failover. I rewrote the change-stream section to state this.
- `gpt-4o-mini` is a model choice, not a service fact. It is now marked as an example default.

### 3. Maintainer skeptic: confirmed (with edits)
The draft names concrete files: a new `skills/sample-scaffold/` folder shaped like `mcp-setup/`, plus exact one-line edits to existing SKILL.md files. Most of it is specific to Azure DocumentDB: the `retrywrites=false` connection string, the MCP opt-in flags, `cosmosSearch` dims matching, `explain()` verification and change-stream resume caveats. It also fixes two real kit defects. I trimmed the parts a maintainer would reject as generic hygiene with no DocumentDB angle: the packaging note and synthetic-data note are removed, and the retry/concurrency and agent-memory bullets now carry DocumentDB-specific index/type guidance. The theme's bucket is `learn-doc_gap`, but the right target is `Azure/documentdb-agent-kit`, which the front matter already names. Learn quickstarts are not the place for a scaffold-skill convention.

## Finding ids

- F0545
- F0614
- F0618
- F0650
- F0682
- F0683
- F0712
- F0718
- F0743
- F0779
- F0783
- F0810
- F0811
- F0814
- F0839
- F0907
- F0957
- F0961
- F0991
- F1023
- F1025
- F1056
- F1057
- F1059
- F1060
- F1061
- F1093
- F1451
- F1575
- F1609
- F1771
- F1810
- F1813
- F1848
- F1907
- F1908
- F1913
- F1935
- F1936
- F1938
- F1968
- F2310
- F2342
- F2372
- F2409
- F2572
- F2606
- F2607
- F2670
- F2671
- F2759
- F2792
- F2831
