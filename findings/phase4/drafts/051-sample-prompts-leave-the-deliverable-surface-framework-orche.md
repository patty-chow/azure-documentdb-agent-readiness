---
title: Add a shared "Deliverable shape" preamble to the starter prompts, and stop grading vector-search bullets on samples without vector search
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P1
sample_count: 21
findings: 24
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: out_of_scope
---

# Add a shared "Deliverable shape" preamble to the starter prompts

> Retargeted: the findings were tagged `learn-docs`, and the earlier draft named a non-existent repo
> (`sample-prompts-spreadsheet`). None of the asks are Azure DocumentDB documentation questions. The
> fix lives in the experiment harness, which owns the spreadsheet importer (`loop/import_samples.py`),
> the requirements drafter (`loop/draft_requirements.py`) and the per-sample `requirements/*.md` files.
> The spreadsheet's Starter Prompt column can carry the same text if its owners prefer.

## What happens today

Each starter prompt (one cell group per sample in the Azure DocumentDB Samples spreadsheet, written by
`loop/import_samples.py` to `samples/<vertical>/NN-<slug>.md` with nothing else in the file) names the
language, framework family and DocumentDB feature. For example `samples/retail/20-store-locator-with-geospatial-search.md`
asks for a Node.js Mongoose service with a 2dsphere index and a `/nearby` endpoint that runs `$geoNear`,
but does not say whether latitude/longitude arrive as query parameters or a body, what the response JSON
looks like, or what counts as done.

In the 100-sample gpt-5-mini run, the cold readiness stage logged 24 information gaps on 21 distinct
samples that are deliverable-shape decisions, not DocumentDB questions:

| Open decision | Samples hit |
|---|---|
| CLI vs REPL vs library vs HTTP API / how the agent is invoked | 02-transaction-categorization-agent, 03-core-banking-transaction-ledger, 08-regulatory-compliance-rag-checker, 10-multi-tenant-storefront-saas, 13-product-q-a-chatbot-rag, 14-hyper-personalized-content-engine, 14-telehealth-session-summarizer, 18-adverse-event-reporting-pipeline, 18-sanctions-list-screening-agent |
| Python web framework, routes and response shape | 19-option-chain-data-store, 15-cohort-analysis-backend |
| Middleware vs client wrapper | 20-open-banking-api-cache-layer |
| Scheduler and timezone for nightly/weekly jobs | 19-insider-threat-detection-pipeline, 20-interest-accrual-batch-processor |
| Real provider vs stub for send / portfolio tools | 19-proactive-outreach-orchestration, 15-financial-advisor-chatbot-rag |
| Concurrency model and per-agent output schema | 09-inventory-reorder-multi-agent-system, 18-returns-refund-workflow-orchestration |
| Query-vs-body, lat/lon naming, error shape; definition of done | 20-store-locator-with-geospatial-search |
| Return similarity score? Citation format? | 13-chronic-disease-risk-predictor, 13-product-q-a-chatbot-rag |
| Env var name for the embedding provider | 20-provider-directory-semantic-search |
| Test strategy (live cluster vs mock) | 20-open-banking-api-cache-layer |

## Why it matters

1. **Builder effort goes to non-DocumentDB decisions.** The experiment measures whether an agent builds
   correctly on Azure DocumentDB with the Agent Kit and MCP servers. These 24 gaps are "the prompt didn't
   say, I'll pick FastAPI / query params / midnight UTC / a stub", which dilutes the signal the run is
   after (resource type, vector index syntax, auth).
2. **The audit grades the wrong surface.** `gallery_section()` in `loop/draft_requirements.py` copies one
   static "What a gallery sample also needs" block (taken from the retail vector-search example) into every
   `requirements/<sample>.md`. That block includes "The vector index dimensions match the embedding model's
   output", "`/search` returns a clear error for an empty query...", and "Search results include the
   similarity score". On samples with no vector search the auditor cannot grade them: in
   `runs/15-cohort-analysis-backend/20261124-205336/05-audit.json` all four are `not_checkable`, and in
   `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json` all four are `not_met`.
3. **Gallery consistency.** Without a default, the shipped samples become a mix of CLIs, REPLs, Flask and
   FastAPI apps with incompatible response shapes.

`prompts/rubric.md` already names the relevant items (11 App surface, 13 Run and test instructions,
14 Definition of done), and `prompts/prompt_reviewer.md` deliberately accepts `sufficient_with_assumptions`.
That is right for DocumentDB knowledge gaps; for shape decisions with no DocumentDB-specific answer the
gallery simply needs a house convention.

## Proposed change

1. **Shared preamble.** Add a `samples/_deliverable-shape.md` (or a "Common prompt preamble" cell in the
   spreadsheet) and have `loop/import_samples.py` append it to every generated `samples/<vertical>/NN-*.md`
   (or have `main.py run` append it at build time so the prompt files stay a verbatim copy of the sheet).
   Suggested text; edit the defaults but keep them concrete:

```
Deliverable shape (applies unless the prompt above says otherwise):
- Surface: a small HTTP API (FastAPI for Python, Express for Node.js) plus one script or CLI
  command that exercises it end to end. Agents and pipelines are invoked through that API or script.
- Scheduled work: run in-process (APScheduler / node-cron) with the cron string in the README and
  times in UTC; the README notes how to move it to an Azure Functions timer trigger.
- External providers (email, SMS, push, brokerage, payments, OCR): call a stub behind an interface;
  list the real provider's settings in .env.example; tests never call a live provider.
- Multi-agent flows: run agents sequentially unless the prompt says otherwise; each agent returns
  JSON matching a schema documented in the README (fields, types, example).
- HTTP contract: GET with query parameters for reads, JSON body for writes; coordinates are `lat`
  and `lon` in the API (GeoJSON stores [lon, lat]); errors are {"error": string, "detail": string}
  with a 4xx/5xx status.
- Vector / RAG responses: each hit carries its similarity score, projected after the
  $search/cosmosSearch stage with {"$meta": "searchScore"}; grounded answers include a `sources`
  array of {id, chunk_id, snippet}.
- Done means: the README ends with an "Acceptance checklist" of 3-6 verifiable statements
  (e.g. "GET /nearby?lat=&lon=&radiusMeters= returns stores nearest-first with distanceMeters,
  openingHours and stock").
```

   Credentials-from-environment, `.env.example`, and "unit tests run without a live cluster" are already in
   the shared gallery section, so the preamble does not repeat them. Per-sample prompts then state only
   what differs (e.g. "CLI REPL instead of HTTP" for a chat sample).

2. **Conditional gallery bullets.** In `loop/draft_requirements.py`, split `gallery_section()` into a
   common part and a vector-search part (index dimensions, index parameters, `/search` errors, similarity
   score) that is included only when the sample's concepts or prompt name vector search, and add bullets
   derived from the preamble (surface, acceptance checklist) so the auditor grades the surface that was
   actually asked for. Regenerate the affected `requirements/*.md`.

## Evidence (run folders)

- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json` - "API surface choices for /nearby endpoint", "Definition of done / acceptance tests"
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json` and `05-audit.json` - "Exact endpoint and response shape for cohort API"; four vector/`/search` bullets `not_checkable`
- `runs/19-proactive-outreach-orchestration/20261124-205844/02-readiness.json` and `05-audit.json` - "Send-agent integrations and safe defaults"; four vector/`/search` bullets `not_met`
- `runs/13-product-q-a-chatbot-rag/20261125-055422/02-readiness.json` - "Choice of RAG app surface (CLI REPL vs HTTP)"; `20261124-184527` - "Citation format for grounded answers"
- `runs/20-open-banking-api-cache-layer/20261124-192737/02-readiness.json` - "Middleware vs wrapper choice", "Automated tests strategy (mock vs live)"
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` - "Agent output schemas"
- `runs/20-interest-accrual-batch-processor/20261124-202826/02-readiness.json` - "Default cron schedule/timezone"

## Verification

### 1. Already covered? - partially_covered

- Learn (https://learn.microsoft.com/en-us/azure/documentdb/vector-search) documents the DocumentDB pieces
  the preamble relies on (cosmosSearch `$search`, projecting `{"$meta": "searchScore"}`), but no Learn page
  prescribes a sample's app surface, scheduler or response contract, nor should it; the findings' `learn-docs`
  tag is a misclassification.
- Harness: `prompts/rubric.md` already lists "11. App surface", "13. Run and test instructions",
  "14. Definition of done - acceptance criteria someone can check", so the gap is detected but not filled.
  The shared gallery block (e.g. `requirements/15-cohort-analysis-backend.md`) already covers env-var
  credentials, `.env.example`, seed script and "Unit tests run without a live cluster". No default
  surface/scheduler/stub/output-schema/acceptance-checklist convention exists in `loop/import_samples.py`,
  `prompts/builder.md` or the sample files. Draft trimmed to avoid repeating the covered items.

### 2. Is the premise true? - confirmed (minor evidence corrections applied)

- 24 findings on 21 distinct samples: confirmed against `scratchpad/phase4/findings-default.json`.
- Static gallery block with vector bullets on non-vector samples: confirmed in `loop/draft_requirements.py`
  (`gallery_section()` reads one example file) and in the two `05-audit.json` files cited above.
- `$meta: "searchScore"` after `$search`/`cosmosSearch` is the documented way to return similarity scores
  (Learn vector-search page, IVF section: "use the `$project` operator to include `searchScore`").
- Corrected: the previous draft's "looser scan of all 120 run folders finds ~40 samples" was unverifiable;
  `runs/` holds 221 timestamped run folders across 104 sample directories. The claim was removed.
- Corrected: the previous draft's preamble proposed a `DOCUMENTDB_URI` and Azure OpenAI env-var set; credentials
  from environment are already required by the gallery block, so the line was dropped rather than inventing names.
- Clarified that GeoJSON stores coordinates as [lon, lat] while the API names them `lat`/`lon`.

### 3. Maintainer skeptic - out_of_scope (retargeted)

As a Microsoft Learn maintainer I would close this: it asks for sample-template conventions, not service
documentation, and the draft's repo `sample-prompts-spreadsheet` does not exist. As maintainer of the
harness (github.com/abinav2307/azure-documentdb-agent-readiness) I would accept it: it names the files
(`loop/import_samples.py`, `loop/draft_requirements.py`, `requirements/*.md`), gives concrete text, and the
conditional-gallery fix corrects a real grading defect visible in two audits. Repo changed to the harness.

## Finding ids

F0330, F0361, F1349, F1444, F1667, F2199, F2259, F2301, F2400, F2470, F2496, F2564, F3024, F3082, F3124, F3272, F3306, F3333, F3402, F3437, F3440, F3470, F3507, F3509
