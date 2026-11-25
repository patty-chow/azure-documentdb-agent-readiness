---
title: "Pin down fixtures, schemas, design defaults and literal framework usage in 15 underspecified starter prompts"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P1
sample_count: 15
findings: 17
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: out_of_scope
---

# Pin down fixtures, schemas, design defaults and literal framework usage in 15 underspecified starter prompts

> Repo note: the draft targeted "sample-prompts-spreadsheet", which is not a repository. The starter prompts live in this harness repo as `samples/<vertical>/<slug>.md` (indexed by `samples/index.json`) and the auditor's checklist as `requirements/<slug>.md`, so the issue is filed here.

## What happens today

Each starter prompt (`samples/<vertical>/<slug>.md`) is a single paragraph that names a framework or an outcome but gives the builder nothing it can fail against. Builders fill the blanks from model priors, and the auditor then files the resulting divergence as a *Microsoft Learn documentation gap*, although none of these items is Azure DocumentDB product documentation; they are application-design decisions the prompt should have made.

Note that `requirements/<slug>.md` already makes the framework usage checkable for the auditor (for example, 01-fraud-detection: "A LangChain tool performs the vector search against Azure DocumentDB"; 10-drug-formulary: "use LlamaIndex to generate the embedding vectors"), and the audits did mark those lines `not_met`. The builder never sees `requirements/<slug>.md`, so the missing piece is in the builder-facing starter prompt.

Two patterns dominate the 17 findings in this theme (15 distinct samples):

**1. The named framework is silently dropped.** Across the 100 samples, 46 starter prompts mention LangChain and 16 mention LlamaIndex. In the latest run of each, a grep for import statements (`from|import langchain…`, `require/import '@langchain…'`, `from|import llama_index…`, excluding `node_modules`/`.venv`) finds no LangChain import in about 21 of the 46 builds and no LlamaIndex import in 13 of the 16. In this theme:

| Sample | Prompt asks for | What was built |
|---|---|---|
| fintech 01 fraud-detection | "Python LangChain agent ... uses a vector search tool" | CLI script, `vector_search()` never wrapped as a Tool, no langchain import |
| banking 07 mortgage multi-agent | "Node.js LangChain multi-agent pipeline" | three plain JS modules; `package.json` mentions LangChain only in its `description`, no `langchain`/`@langchain/*` dependency; builder calls them "LangChain-style agents" |
| customer-360 08 segmentation | "LangChain agent with a DocumentDB aggregation tool" | `compute_metrics()` exists but is never registered as a Tool |
| customer-360 14 complaint classifier | "Python LangChain agent using Beanie" | `langchain` is listed in requirements.txt and an unused `src/pipeline.py` imports it, but the pipeline actually run (`src/app/pipeline.py`) calls `openai.ChatCompletion.create` directly |
| healthcare 10 drug formulary | "Python LlamaIndex service" | `llama-index==0.14.26` pinned in requirements.txt, but `openai.Embedding.create` is used in `main.py`, `scripts/seed_data.py` and `scripts/query_demo.py` |

None of these builds logs a decision of the form "dropped LangChain/LlamaIndex because X"; the prompt simply gives the builder nothing that *fails* when the import is missing.

**2. A design parameter is left open and the builder invents it.**

| Sample | Open parameter | What the builder picked (all `model_default`) |
|---|---|---|
| fintech 01 AML detector | fixture transactions per typology, expected detections | ad-hoc seed, no acceptance criteria |
| healthcare 02 clinical trial matching | eligibility criteria schema | unvalidated nested object, no `$jsonSchema` |
| retail 09 inventory reorder | document shapes, seed sizes | 30 SKUs, 14 days of sales, field names chosen per agent |
| fintech 11 market-news | notification payload, auth | invented payload + bearer token; delivery never exercised |
| customer-360 11 consent store | retention default | 365 days |
| healthcare 19 care coordination | provenance for generated care plans | none recorded |
| retail 19 cross-sell (two runs) | affinity formula; request-time vs precomputed basket embedding | invented heuristic; averaged stored embeddings instead of embedding the basket per request (which `requirements/19-cross-sell-recommendation-beanie.md` expects) |
| fintech 19 option chain | pagination for "full chain" endpoint | none, whole chain returned |
| customer-360 19 proactive outreach | send-agent provider | TODO stub, sandboxed |
| banking 20 open-banking cache | demo TTL | TTL 5 s, stale window 10 s |

## Why it matters

- 15 of 100 samples are in this theme; the framework-drop pattern reaches roughly a third of all samples when counted across every LangChain/LlamaIndex prompt.
- The gallery promises "a LangChain sample" or "a LlamaIndex sample"; many of the builds do not contain the library, so they do not demonstrate the Learn integration pages they should drive readers to.
- Every open parameter became a `model_default` decision, which the auditor logs as a doc gap. These 17 findings landed in the `learn-docs` bucket and dilute the real Learn gaps.
- Different builders produce incompatible schemas and formulas for the same sample, so reruns are not comparable and reviewers cannot keep a stable acceptance checklist.

## Proposed change

Amend the starter prompt in `samples/<vertical>/<slug>.md` for the 15 samples below (one or two added sentences each), and add the matching bullet under "What the starter prompt asks for" in `requirements/<slug>.md` where it is not already there (the framework bullets already exist). Suggested text:

- **fintech 01 fraud-detection** (`samples/fintech/01-fraud-detection-with-vector-similarity.md`): "Expose `vector_search` as a LangChain `Tool` (or `@tool`) and invoke it from a LangChain agent; see the LangChain section of https://learn.microsoft.com/azure/documentdb/build-rag-applications#langchain-azure-documentdb-integration. The `langchain` import must appear in the agent entry point."
- **banking 07 mortgage** (`samples/banking/07-mortgage-application-multi-agent.md`): "Each of the three agents is a LangChain.js agent or Runnable (`langchain` / `@langchain/*` packages) and the orchestrator composes them with LangChain; the packages must be dependencies in package.json and imported in the orchestrator. Use the `mongodb` driver for Azure DocumentDB access." (The Learn LangChain page's vector-store integration is Python-only and tells TypeScript apps to use the `mongodb` driver, so do not link it as the Node.js pattern. Also drop the generic `/search` lines from this sample's requirements.md; see harness note below.)
- **customer-360 08 segmentation**: "Register the aggregation function as a LangChain `Tool` named `documentdb_aggregate` and pass it to the agent."
- **customer-360 14 complaint classifier**: "Classification runs through a LangChain `PromptTemplate` and chat model in the code path the app actually executes (not a direct OpenAI SDK call)."
- **healthcare 10 drug formulary**: "Embeddings for both seeding and queries are produced through LlamaIndex's embedding interface (`Settings.embed_model`), per https://learn.microsoft.com/azure/documentdb/query-knowledge-base#llamaindex-azure-documentdb-integration; the OpenAI SDK must not be called directly."
- **fintech 01 AML detector**: "Seed a fixture set of about 60 transactions across 8 accounts that contains exactly one structuring chain, one rapid pass-through chain and one 3-hop cycle; the agent must flag those three and nothing else. Ship the fixtures as JSON and assert the three detections in a test."
- **healthcare 02 clinical trial matching**: "Trial documents follow a fixed schema (`trialId`, `title`, `criteria.inclusion[]`, `criteria.exclusion[]`, each `{field, op, value}`, `embedding: number[]`) enforced with a `$jsonSchema` collection validator."
- **retail 09 inventory reorder**: "Collections `sales_velocity {sku, date, units}`, `lead_times {supplierId, sku, days, unitCost}`, `purchase_orders {poId, sku, supplierId, qty, createdAt}`; the seed script loads 30 SKUs, 3 suppliers and 14 days of sales and accepts `--scale small|medium|large`."
- **fintech 11 market-news**: "Notifications are HTTP POSTs to `WEBHOOK_URL` with body `{alertId, ticker, headline, sentiment, articleId, firedAt}` and an `Authorization: Bearer $WEBHOOK_TOKEN` header; include a local receiver script that records deliveries so a test can assert one fired alert."
- **customer-360 11 consent store**: "Retention defaults to 365 days via `CONSENT_RETENTION_DAYS`; the README states that the value is a demo default, not legal guidance."
- **healthcare 19 care coordination**: "Every care plan document carries `provenance {model, promptTemplateId, embeddingModel, generatedAt, sourceDocIds[]}`."
- **retail 19 cross-sell**: "Embed the incoming basket with OpenAI at request time and query with a `$search` / `cosmosSearch` aggregation; rank by `affinity = 0.6 * similarityScore + 0.4 * log1p(coPurchaseCount) / log1p(maxCoPurchaseCount)` and return the components with each candidate."
- **fintech 19 option chain**: "The full-chain endpoint pages with keyset pagination on `strike` (`?after=<strike>&limit=200`) and returns `nextToken`."
- **customer-360 19 proactive outreach**: "Provide `providers/smtpProvider.js` and `providers/twilioProvider.js` behind a `SEND_MODE=sandbox|live` switch; sandbox is the default and live requires `SMTP_*` / `TWILIO_*` env vars listed in `.env.example`."
- **banking 20 open-banking cache**: "Default `CACHE_TTL_SECONDS=5` and `STALE_WINDOW_SECONDS=10` for the demo, documented in the README with a note on choosing production values."

Where literal framework usage is the point, the prompt should also say the fallback is not allowed: an explicit "do not call the OpenAI SDK directly" sentence gives the builder a requirement it can see, matching the `requirements/<slug>.md` line the auditor already checks.

**Harness note:** 101 of the 102 files in `requirements/` carry the boilerplate gallery lines "`/search` returns a clear error for an empty query and when the embedding call fails" and "Search results include the similarity score", including the mortgage pipeline (`requirements/07-mortgage-application-multi-agent.md` lines 27-28), which has no search endpoint; that produced finding F1119 ("add a POST /search route"). It also names `/search` for samples whose prompt specifies a different route (e.g. `/formulary-search`). Make those lines conditional on the prompt asking for a search endpoint and use the prompt's route name.

**Not proposed:** a Learn page for any of these items. Affinity formulas, webhook schemas, consent retention periods, demo TTLs and trial-eligibility schemas are application design, not Azure DocumentDB behaviour; the Learn LangChain and LlamaIndex pages already exist and should be linked from the Python prompts rather than duplicated.

## Evidence

- `runs/10-drug-formulary-semantic-search/20261124-194440/05-audit.json` (LlamaIndex requirement `not_met`); `app/main.py` line 29, `app/scripts/seed_data.py` line 34 call `openai.Embedding.create`
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/doc-gaps.md` (vector_search never wrapped as a LangChain Tool)
- `runs/07-mortgage-application-multi-agent/20261124-201025/doc-gaps.md` and `app/package.json` (LangChain only in the description field; spurious `/search` gap from requirements boilerplate)
- `runs/14-customer-complaint-classifier/20261124-201931/05-audit.json`; `app/src/app/pipeline.py` line 24 (direct `openai.ChatCompletion.create`)
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/doc-gaps.md` and `runs/19-cross-sell-recommendation-beanie/20261125-055705/doc-gaps.md` (invented affinity formula; basket embedding diverged from requirements)

## Verification

### 1. Already covered? partially_covered

- The auditor-side checklist already contains the framework requirements: `requirements/01-fraud-detection-with-vector-similarity.md` ("A LangChain tool performs the vector search against Azure DocumentDB..."), `requirements/10-drug-formulary-semantic-search.md` ("use LlamaIndex to generate the embedding vectors..."), `requirements/08-dynamic-segmentation-engine.md` ("registered as a LangChain tool"), `requirements/14-customer-complaint-classifier.md`, `requirements/07-mortgage-application-multi-agent.md` line 11. `requirements/19-cross-sell-recommendation-beanie.md` already requires embedding the basket per request. The draft's request to "mirror in requirements.md so the auditor can fail it" is therefore already done for the framework items; the body was corrected to say so.
- Not covered: the builder-facing starter prompts (`samples/*/<slug>.md`, e.g. `samples/fintech/01-fraud-detection-with-vector-similarity.md`) contain none of the fixtures, schemas, formulas, payloads, pagination, provenance or default values, and do not say the framework import is mandatory. `requirements/` contains no fixture sets, formula, payload schema or default values either.
- The Learn integration sections the prompts should link exist: https://learn.microsoft.com/en-us/azure/documentdb/build-rag-applications (heading "LangChain Azure DocumentDB integration") and https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base (heading "LlamaIndex Azure DocumentDB integration").

### 2. Premise true? confirmed (with corrections applied)

Core premise holds: the prompts name a framework or outcome without checkable specifics, and the builds drop them. Corrections applied to the body:
- Counts: the draft said 14 of 46 LangChain builds and 14 of 17 LlamaIndex builds lack the import. `grep -il` over `samples/*/*.md` finds 46 LangChain and 16 LlamaIndex prompts; an import grep over the latest run of each finds roughly 21/46 and 13/16 without an import. The unverified "6 do not list it as a dependency" and "~2,900 findings" figures were removed.
- Mortgage: confirmed no LangChain dependency (`package.json` mentions LangChain only in `description`).
- Complaint classifier: `langchain` *is* in requirements.txt and an unused `src/pipeline.py` imports it; the executed `src/app/pipeline.py` calls OpenAI directly. Table corrected.
- Drug formulary: confirmed `llama-index==0.14.26` pinned and `openai.Embedding.create` in `main.py`, `scripts/seed_data.py`, `scripts/query_demo.py`.
- Node.js: both Learn pages state the vector-store integration is Python-only and point TypeScript apps to the `mongodb` driver with `$search` + `cosmosSearch`; the mortgage suggestion now names LangChain.js packages and does not link the Python Learn page.
- `/search` boilerplate confirmed in 101 of 102 `requirements/*.md` files, including the mortgage file (lines 27-28).
- DocumentDB facts used (cosmosSearch via `$search`, `number[]` embeddings, `$jsonSchema` validator, TTL indexes) are consistent with the service.

### 3. Maintainer skeptic: out_of_scope (re-homed to abinav2307/azure-documentdb-agent-readiness)

The draft named "sample-prompts-spreadsheet", which is not a repository and not a defined target; the theme is filed under `learn-doc_gap` but explicitly asks for no Learn change, so it is out of scope for Learn, the agent kit and the MCP server. The prompts and requirements live in the harness repo (`samples/`, `requirements/`), and the issue names exact files and exact sentences to add, plus a concrete harness fix for the `/search` boilerplate. As maintainer of the harness I would accept it with the edits above. Repo in the front matter changed accordingly.

## Finding ids

F0019, F0063, F0237, F1119, F1123, F1216, F1506, F1605, F1845, F1877, F2344, F3163, F3194, F3245, F3310, F3345, F3450
