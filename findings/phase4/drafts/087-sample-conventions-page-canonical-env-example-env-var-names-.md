---
title: "Add `documentdb-sample-conventions` skill: canonical .env.example contract, default chat/embedding models + EMBEDDING_DIMS, stub mode, and a one-line 'defaults used' log"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 25
findings: 27
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add `documentdb-sample-conventions` skill: canonical `.env.example` contract, default chat/embedding models + `EMBEDDING_DIMS`, stub mode, and a one-line "defaults used" log

## What happens today

The kit explains DocumentDB features well, but nothing in it tells an agent **how a generated sample should be configured**. There is no page that says:

- which environment variables a sample declares and what they are called (the kit itself is split: `skills/connection/SKILL.md` and `skills/local-deployment/local-env-driven-config.md` use `DOCUMENTDB_URI` (9 occurrences), while `compat/PROMPT.md`, `compat/QUICKSTART.md`, `scenarios/ecommerce-advanced/README.md` and the code behind them (`compat/src/database.js`, `scenarios/ecommerce-advanced/scripts/load.mjs`) use `MONGODB_URI`);
- which LLM provider, chat model, embedding model and **embedding dimension** to default to when the user does not say (the vector rules all show `dimensions: 1536` / `text-embedding-3-small` as examples, but no rule says "use this unless told otherwise, and read it from an env var");
- whether a sample's tests/CI should call a real LLM or a deterministic stub;
- how to record a choice the prompt left open (provider, model, Python minor, framework, scheduler, and so on), so the sample stays inspectable.

The closest existing content is `skills/local-deployment/local-env-driven-config.md`, which covers only `DOCUMENTDB_URI` + `DOCUMENTDB_ALLOW_INVALID_CERTS` (and whose managed-cluster example uses the host `<cluster>.mongocluster.documentdb.azure.com` and omits `retrywrites=false&maxIdleTimeMS=120000`; the documented host is `<cluster>.mongocluster.cosmos.azure.com`), and `skills/vector-search/vector-normalize-embeddings.md`, which already stores `embeddingModel`/`embeddingDims` on documents but does not say where those values should come from.

## Why it matters

In a 100-prompt run (gpt-5-mini, kit skills + DocumentDB/Azure/Learn MCP servers), **25 of 100 samples** produced an audit finding that traces to this missing page (27 findings). The agent did not hallucinate DocumentDB facts here; it simply had no contract and guessed differently each time, producing real bugs:

- `09-lead-scoring-agent`: `.env.example` declares `OPENAI_MODEL`, `scoreLead.js` reads `OPENAI_CHAT_MODEL`. Copying the template silently ignores the setting.
- `06-collateral-management-store`: code reads `DB_NAME` (fallback `sample_banking_06`), `.env.example` omits it; the seed connected to the wrong database until the builder noticed.
- `07-customer-review-sentiment-pipeline`: two `run_pipeline` implementations in one sample read different names (`DATABASE_NAME` vs the other), `MODEL` never templated.
- `08-personalized-email-campaign-builder`, `16-atm-network-status-monitor`: runtime toggles the code reads (`USE_OPENAI`, `SEED_ATMS`, `PORT`) never appear in `.env.example`, so following the README cannot reach them.
- `18-sanctions-list-screening-agent`, `10-wealth-management-rag-portal`: `dimensions: 1536` hard-coded into `createIndexes` with `cosmosSearchOptions`; swapping the embedding model breaks index creation or every query with a dimension mismatch and there is no `EMBEDDING_DIMS` to change.
- `11-market-news-sentiment-orchestration`, `12-clv-prediction-pipeline`: no `OPENAI_API_KEY` in the run environment and no stub path, so the LLM step was never executed or verified; `14-loan-origination-workflow-orchestration` went the other way and stubbed everything, recorded only as `model_default`.
- `19-insider-threat-detection-pipeline`: when the embedder was unreachable the sample persisted empty embeddings with no marker, so there is no way to backfill.

Across the 25 samples, ~20 decisions (provider, chat model, embedding model/dims, Python 3.11, FastAPI, seed size, hourly refresh, midnight UTC cron, REST+CLI, middleware+wrapper, BufferMemory, hard-coded reference ranges) were logged with reason `model_default` and no rationale, so samples are inconsistent with each other and un-inspectable after the fact.

## Proposed change

One PR: four files added under `skills/sample-conventions/`, two registration tables touched, and a small consistency pass over existing kit files. Everything below is consistent with facts already in the kit (`cosmosSearch` kinds `vector-ivf` / `vector-hnsw` / `vector-diskann`, vectors stored as `number[]`, `mongodb+srv://...mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`).

### 1. `skills/sample-conventions/SKILL.md` (new, standalone skill)

```markdown
---
name: documentdb-sample-conventions
description: Conventions for generating a runnable Azure DocumentDB sample or quickstart app — canonical environment variable names and a complete .env.example, default LLM provider / chat model / embedding model and EMBEDDING_DIMS for cosmosSearch indexes, deterministic stub mode for CI, baseline framework/seed/scheduler defaults, and how to record a departure from a default. Use whenever asked to build, scaffold or generate a sample, demo, starter or gallery app that connects to Azure DocumentDB.
license: MIT
---

# Sample conventions — Azure DocumentDB

Apply these when generating a sample. They make samples consistent with each other,
runnable from `.env.example` alone, and inspectable after the fact.

## Rules

- [sample-env-contract](sample-env-contract.md) — Canonical variable names; `.env.example` lists **every** variable the code reads, one commented line each; copy `env.example`.
- [sample-llm-defaults](sample-llm-defaults.md) — Default provider/models, `EMBEDDING_DIMS` drives index creation, `LLM_PROVIDER=stub` for CI, `needs_embedding` backfill.

## Record departures (two lines)

Every sample README has a `## Defaults used` table. Add one row whenever you depart
from a default on this page or pick a value the prompt left open (for example Python minor, web framework, scheduler, seed size):

| Choice | Value | Why (one line) |
|---|---|---|
| embedding model | text-embedding-3-large / 3072 | prompt asked for maximum recall on legal text |

If a builder keeps a machine-readable decision log, mirror the same one-line reason there.
```

### 2. `skills/sample-conventions/env.example` (new; samples copy it to `.env.example`)

```dotenv
# ---- DocumentDB ------------------------------------------------------------
# Azure DocumentDB connection string (Connection strings blade). Never commit a real one.
DOCUMENTDB_URI=mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
# Database the sample creates/uses.
DB_NAME=sample_app
# Local container only (self-signed cert). Leave unset against a real cluster.
# DOCUMENTDB_ALLOW_INVALID_CERTS=true

# ---- LLM / embeddings -------------------------------------------------------
# stub | openai | azure-openai. Default stub = deterministic, no key needed, used by tests/CI.
LLM_PROVIDER=stub
# openai
OPENAI_API_KEY=
# azure-openai (CHAT_MODEL / EMBEDDING_MODEL then hold the *deployment* names)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=2024-10-21
# Models. Change EMBEDDING_DIMS together with EMBEDDING_MODEL; the vector index is created from it.
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMS=1536

# ---- Vector index (cosmosSearch) ------------------------------------------
# vector-diskann | vector-hnsw | vector-ivf  (see documentdb-vector-search for sizing)
VECTOR_INDEX_KIND=vector-hnsw
# COS | L2 | IP
VECTOR_SIMILARITY=COS

# ---- Runtime --------------------------------------------------------------
PORT=3000
LOG_LEVEL=info
```

### 3. `skills/sample-conventions/sample-env-contract.md` (new rule, kit rule shape)

- **Why it matters:** the five mismatch cases above (one paragraph).
- **Incorrect:** `.env.example` with `OPENAI_MODEL=` while code reads `process.env.OPENAI_CHAT_MODEL`; `DB_NAME` read with a fallback but not templated.
- **Correct:** names from `env.example`; **every** variable the code reads appears in `.env.example` with a comment and a safe placeholder; no secrets in placeholders; `DB_NAME` always present even when a fallback exists; same names in every script of the sample.
- **Optional lint (one line, add to the sample's test script):**
  ```bash
  diff <(grep -rhoE 'process\.env\.[A-Z0-9_]+|os\.(getenv|environ(\.get)?)\(["'"'"'][A-Z0-9_]+' src scripts | grep -oE '[A-Z][A-Z0-9_]+' | sort -u) <(grep -oE '^#? ?[A-Z][A-Z0-9_]+=' .env.example | tr -d '# =' | sort -u)
  ```
- **References:** `local-env-driven-config.md`, 12factor config.

### 4. `skills/sample-conventions/sample-llm-defaults.md` (new rule)

- **Defaults:** `LLM_PROVIDER=stub` for tests/CI; `openai` with `gpt-4o-mini` + `text-embedding-3-small`/1536 when the user wants real calls; `azure-openai` uses the same two model vars as deployment names. State that these are *sample* defaults, not a service recommendation, and that the chat model should be swapped for a currently available one when it is retired (only `CHAT_MODEL` changes; the vector index depends only on `EMBEDDING_MODEL`/`EMBEDDING_DIMS`).
- **Rule:** create the `cosmosSearch` index from `EMBEDDING_DIMS`, never a literal:
  ```javascript
  const dims = Number(process.env.EMBEDDING_DIMS ?? 1536);
  await db.command({ createIndexes: 'docs', indexes: [{ name: 'embedding_idx', key: { embedding: 'cosmosSearch' },
    cosmosSearchOptions: { kind: process.env.VECTOR_INDEX_KIND ?? 'vector-hnsw', similarity: process.env.VECTOR_SIMILARITY ?? 'COS', dimensions: dims, m: 16, efConstruction: 64 } }] });
  // store vectors as plain number[] — BSON binary vectors are not indexed
  ```
- **Stub mode:** `embed(text)` returns a deterministic `number[]` of length `EMBEDDING_DIMS` (seeded hash -> floats, L2-normalized); `chat(prompt)` returns a canned, schema-valid response; tests run with stub; a `test:live` script sets `LLM_PROVIDER=openai` and is skipped when the key is missing.
- **Key handling:** read keys from env only, never log or echo them, never persist prompts with keys; mention a simple per-process rate limiter when the sample exposes LLM calls over HTTP.
- **Embedder outage / backfill:** on embedder failure persist the document with `embedding: null, needs_embedding: true`, index `{ needs_embedding: 1 }`, ship a `backfill` script that embeds and unsets the flag. Record `embeddingModel`/`embeddingDims` per document as in `vector-normalize-embeddings.md`.

### 5. Registration and consistency edits

- `AGENTS.md` -> "Interactive / workflow skills" table: `| documentdb-sample-conventions | skills/sample-conventions/ | Generating a sample/demo/starter app: env var names, .env.example, default LLM/embedding models and dims, stub mode, baseline defaults |` and a routing hint `**Building / scaffolding a sample or demo app** -> documentdb-sample-conventions`.
- `docs/SKILLS.md` -> "Standalone SKILL.md skills" table: same row.
- `compat/PROMPT.md`, `compat/QUICKSTART.md`, `scenarios/ecommerce-advanced/README.md` (5 occurrences) **and** the code they document, `compat/src/database.js` (3) and `scenarios/ecommerce-advanced/scripts/load.mjs` (2): `MONGODB_URI` -> `DOCUMENTDB_URI` so the kit agrees with its own skills (renaming only the docs would break the scenario; optionally read `MONGODB_URI` as a deprecated fallback for one release).
- `skills/local-deployment/local-env-driven-config.md`: change the managed-cluster example host to `<cluster>.mongocluster.cosmos.azure.com` and add `retrywrites=false&maxIdleTimeMS=120000`, matching `env.example`.

Deliberately out of scope: generic framework/runtime defaults (Python minor, FastAPI vs alternatives, seed-size tiers, scheduler, cron timezone, CLI vs REST, memory store, middleware vs wrapper). Those are not DocumentDB-specific and belong to whoever owns the sample gallery or the generation harness; this PR only requires that such choices be recorded in the `## Defaults used` table.

## Evidence (run folders)

- `runs/09-lead-scoring-agent/20261124-204408/doc-gaps.md` — `OPENAI_MODEL` in `.env.example` vs `OPENAI_CHAT_MODEL` in code
- `runs/06-collateral-management-store/20261124-200922/05-audit.json` — `DB_NAME` read, not templated
- `runs/07-customer-review-sentiment-pipeline/20261125-054042/doc-gaps.md` — two scripts, two variable names; `MODEL` missing
- `runs/18-sanctions-list-screening-agent/20261124-202645/05-audit.json` — `dimensions=1536` hard-coded in index creation, no `EMBEDDING_DIM`
- `runs/14-loan-origination-workflow-orchestration/20261124-191837/02-readiness.json` — "LLM provider and model choice" / "require live LLM calls?" listed as information gaps before the build
- `runs/16-atm-network-status-monitor/20261124-202405/doc-gaps.md` — `SEED_ATMS`, `PORT` read but absent from `.env.example`; asks for a CI check

## Verification

### 1. Already covered? partially_covered

The kit covers one slice of this and nothing else. `skills/local-deployment/local-env-driven-config.md` says to read the URI from `DOCUMENTDB_URI`, drive TLS relaxation from `DOCUMENTDB_ALLOW_INVALID_CERTS`, and "Keep `.env` out of source control (`.gitignore`); commit `.env.example`." Its `.env.example` lists only those two variables. The vector rules use `dimensions: 1536` / `text-embedding-3-small` only as worked examples: `skills/vector-search/vector-create-diskann-index.md` line 39 has "dimensions: 1536,       // matches text-embedding-3-small", and `skills/vector-search/vector-normalize-embeddings.md` lines 34-35 store `embeddingModel`/`embeddingDims`. No rule tells an agent to read the dimension from an env var or which model to default to. A grep of `skills/` and `knowledge-base/` for `EMBEDDING_DIM`, `LLM_PROVIDER`, `needs_embedding`, `gpt-4o-mini` and `sample convention` returns nothing. The `AGENTS.md` "Interactive / workflow skills" table and the `docs/SKILLS.md` "Standalone SKILL.md skills" table have no sample-scaffolding skill. Target is agent-kit, so Learn pages were not the check target.

### 2. Premise true? confirmed (one count corrected, two omissions added)

- Checked the theme's 27 finding records: they span 25 distinct samples, which matches the draft's 25/100.
- Kit naming split confirmed, with one count corrected. `MONGODB_URI` appears 5 times in `compat/PROMPT.md` (1), `compat/QUICKSTART.md` (3) and `scenarios/ecommerce-advanced/README.md` (1). The draft said `DOCUMENTDB_URI` appears "15 times across skills/". The real count is 9 occurrences in 2 files, and the body now says so.
- Added: `MONGODB_URI` is also read in code, in `compat/src/database.js` (3) and `scenarios/ecommerce-advanced/scripts/load.mjs` (2). The rename has to include those files or the scenario breaks.
- Added: `local-env-driven-config.md` uses the host `mongocluster.documentdb.azure.com` and leaves out `retrywrites=false&maxIdleTimeMS=120000`. The documented Azure DocumentDB format is `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`, so a fix for that file is now part of the PR.
- Technical content checked:
  - `cosmosSearch` kinds `vector-ivf`/`vector-hnsw`/`vector-diskann` are correct.
  - The HNSW options `m` and `efConstruction` and the similarity values `COS`/`L2`/`IP` match the kit's vector rules.
  - Storing vectors as `number[]` is required: BSON binary vectors are not indexed.
  - `text-embedding-3-small` outputs 1536 dimensions by default.
  - `2024-10-21` is a GA Azure OpenAI API version.
- `gpt-4o-mini` is offered as a sample default only. A note now says to swap the chat model when it is retired; the vector index does not depend on it.

### 3. Maintainer skeptic: confirmed (with scope trimmed)

As a kit maintainer I would accept the DocumentDB-specific core:
- an env contract that uses the kit's own `DOCUMENTDB_URI` name
- `cosmosSearch` index creation driven by `EMBEDDING_DIMS`, with vectors as `number[]`
- a deterministic stub embedder sized to the index
- the `needs_embedding` backfill pattern
- fixing the kit's own `MONGODB_URI` and host inconsistencies.

These name concrete files and changes and fix real bugs seen in the samples. I would not accept the original baseline-defaults table (Python 3.11, FastAPI/Express, seed tiers, scheduler, cron timezone, REST+CLI, memory store, middleware vs wrapper). That is generic engineering policy with no DocumentDB angle, so it was removed. Those choices now only have to be recorded in the `## Defaults used` README table, and the body points them to the gallery or harness owner.

## Finding ids

- F0058
- F0335
- F0714
- F0871
- F1058
- F1704
- F1740
- F1844
- F2003
- F2444
- F1319
- F1542
- F1674
- F2666
- F2764
- F3312
- F3409
- F3449
- F2761
- F2899
- F2734
- F3129
- F3278
- F0369
- F0715
- F1091
- F0482
