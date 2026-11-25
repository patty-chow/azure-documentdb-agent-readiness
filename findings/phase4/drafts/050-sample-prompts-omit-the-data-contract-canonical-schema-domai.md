---
title: "Add a "Schema and seed data" block to every sample starter prompt (collections, example docs, seed size, synthetic/licence note, upsert key, domain reference, definition of done)"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P1
sample_count: 63
findings: 78
bucket: learn-information_gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: out_of_scope
---

# Add a "Schema and seed data" block to every sample starter prompt

> Filed against the experiment harness (abinav2307/azure-documentdb-agent-readiness), which owns the sample prompts via the Samples spreadsheet, `loop/import_samples.py` and `samples/`. It is not a Microsoft Learn, Agent Kit or DocumentDB MCP change: per-sample schemas and seed sets are not platform documentation.

## What happens today

Every starter prompt in the Azure DocumentDB Samples spreadsheet describes the *application* (framework, driver, which DocumentDB feature to show) but not the *data contract*. The prompts are 47-128 words long (median 54). Across all 100 prompt files generated from the spreadsheet (`samples/<vertical>/*.md`):

| term | prompts containing it |
|---|---|
| "seed", "fixture", "synthetic", "example document", "acceptance", "definition of done", "licen(se)" | **0 / 100** |
| "upsert" | 3 / 100 |
| "idempotent" | 0 / 100 |
| "collection" | 6 / 100 |
| "field" | 17 / 100 (none give a full field list) |

Meanwhile the run environment handed to the agent says: *"create the collections and indexes, load the sample data, run the queries the sample exists to show"*, and the shared section that the pipeline appends to every sample's reference requirements (`requirements/<NN>-*.md`, which the audit stage scores against; see `loop/draft_requirements.py`) contains the requirement *"A seed script loads sample data and creates the index, and can be run twice without duplicating data."* The agent is held to a data contract that nobody wrote down.

Typical prompt (banking-02, verbatim, 58 words): *"Using the DocumentDB skill, build an async Python SWIFT message ingestion service using Beanie ODM that parses MT103 and MT202 message fields into structured DocumentDB documents, validates required fields, and bulk-writes batches for throughput. Include an aggregation endpoint that summarises daily message volume and total value by message type."* No tag-to-field mapping, no sample message, no "required fields" list, no seed size.

## Why it matters

**Scale.** 78 readiness findings in this theme across **63 of the 100 samples**; widening the pattern match to any schema/seed/dataset information gap, **103 of 120 run readiness reports** flag it. It is the single most common gap in the corpus.

**The agent wastes turns searching for something that cannot exist.** In every cited run the cold-quiz stage reports searching `documentdb-data-modeling`, `documentdb-local-deployment` and Microsoft Learn quickstarts for a canonical schema or seed set and (correctly) finding nothing. One agent searched Learn for a `sample_retail_06` seed dataset that does not exist (runs/06-order-history-timeline-agent/20261124-183612). Another called the DocumentDB MCP `list_databases` to see whether `sample_customer_360_15` already had collections, found none, and had to guess field names (runs/15-cohort-analysis-backend/20261124-205336). These are not doc gaps; they were mis-filed as `learn-docs` findings because the agent looked there.

**Builds are not deterministic or comparable across runs.** Two runs of the same prompt produced incompatible schemas:

| sample | run 1 seed fields | run 2 seed fields |
|---|---|---|
| fraud-detection-with-vector-similarity | `pattern_name`, `vector`, `dims`, `model`, `schemaVersion` | `pattern_id`, `embedding`, `severity`, `tx_id`, `example_transactions` |
| patient-record-summarizer-rag | `chunkId`, `patientId`, `sourceDocId`, `createdAt` (camelCase) | `chunk_id`, `source_doc_id`, `created_at`, `embedding` (snake_case) |
| anti-money-laundering-pattern-detector | `owner`, `linked_tx_ids` | `account_id`, `holder_name`, `sample_seeded`, `seeded_at` |

**The seed requirement fails or half-passes in 37% of audits.** Of 115 audits that checked "seed script can be run twice without duplicating data": 72 met, 36 partly met, 7 not met; 11 audits attribute the miss to `prompt_silent`.

**Domain content only the author can supply is missing.** Agents had to invent: SWIFT MT103/MT202 tag-to-field mapping (`:20:`, `:23B:`, `:32A:`, `:50K:`); a fraud risk-scoring function; the fixed transaction-category taxonomy; the clinical-trial inclusion/exclusion schema; the "coverage ratio" formula and where liabilities live; the applicant shape for credit scoring; whether lab reference ranges are hard-coded or stored; maturity-bucket boundaries for the rate book; the OpenAI extraction JSON schema for KYC. Each of these is a one-paragraph decision the prompt author already knows.

**Compliance risk.** Healthcare and banking prompts say "include sample patient records" / "store known fraud patterns" without saying *synthetic, non-PHI, no real sanctions lists*. The care-gap audit failed partly because the agent dumped seeded patient identifiers straight into an LLM prompt with no redaction (runs/11-care-gap-identification-pipeline/20261124-194646, verdict `fail`).

## Proposed change

Add **one extra "Starter Prompt" row per sample** in the Azure DocumentDB Samples spreadsheet that `loop/import_samples.py` reads (the source of `samples/<vertical>/*.md` in this repository) containing a `Schema and seed data` block. `loop/import_samples.py` already appends extra Starter Prompt rows as additional paragraphs of the prompt file, so no importer or pipeline change is needed; re-running the import regenerates `samples/<vertical>/*.md`.

Template (keep it to 120-200 words; link a fixture file instead of inlining when it is larger than 5 documents):

```
Schema and seed data
- Database: <sample_db_name>. Collections: <name> (<key fields: type>), <name> (...).
- Example documents: 3-5 inline JSON documents, or link to <fixture>.json/.csv.
- Seed: <N> documents (50-500 unless the sample needs more), synthetic, generated by the seed script
  or shipped as the fixture above; CC0. <For clinical/financial samples:> no real PHI/PII, no real
  sanctions or customer data; names and IDs are fabricated.
- Idempotency: the seed script upserts on <natural key> and can be run twice with no duplicates.
- Domain reference the README must reproduce: <formula / tag mapping / taxonomy / bucket boundaries /
  JSON schema>.
- Definition of done: <3-6 checkable assertions, e.g. "GET /summary for 2026-01-15 returns 2 MT103
  and 1 MT202 totalling 1,750,000 USD">.
```

### Worked example 1: banking-02 "SWIFT message parser store"

```
Schema and seed data
- Database: sample_banking_02. Collection swift_messages: message_type ("MT103"|"MT202"),
  message_id (tag :20:, string, unique), bank_op_code (:23B:), value_date (:32A: date part, Date),
  currency (:32A: ISO 4217), amount (:32A:, Decimal128), ordering_customer (:50K:/:50A:),
  beneficiary (:59:), sender_bic, receiver_bic, raw_text, ingested_at.
- Required fields: :20:, :32A:, and :50K:/:50A: (MT103) or :52A:/:58A: (MT202); reject otherwise.
- Example documents: 3 MT103 and 2 MT202 raw messages in seed/swift_samples.txt (synthetic BICs and
  names; no real institutions).
- Seed: 200 synthetic messages across 10 value dates, generated by seed.py; CC0.
- Idempotency: upsert on message_id.
- Definition of done: POST /ingest with the 5 sample messages stores 5 documents; posting them again
  stores 0 new; GET /aggregations/daily-summary returns one row per (value_date, message_type) with
  count and total_amount; a message missing :32A: is rejected with a 400 and is not stored.
```

### Worked example 2: customer-360-15 "Cohort analysis backend"

```
Schema and seed data
- Database: sample_customer_360_15. Collections: customers (_id: string customer id, acquired_at: Date,
  channel: "web"|"store"|"partner"|"referral", first_product: string); events (customer_id, type:
  "purchase"|"login"|"support", occurred_at: Date, product: string); cohort_snapshots (cohort_month,
  computed_at, retention_30/60/90, by_channel{}, by_product{}).
- Example documents: 3 customers and 6 events inline below.
- Seed: 1,000 customers acquired over 12 months, ~8 events each, synthetic; CC0.
- Idempotency: upsert customers on _id, events on (customer_id, type, occurred_at).
- Retention definition: a customer is retained at 30 days if they have any "purchase" event in
  (acquired_at + 30d, acquired_at + 60d].
- Definition of done: GET /cohorts returns 12 cohort rows from cohort_snapshots; the pipeline contains
  a $bucket stage on acquired_at and a $facet stage with channel and product branches; POST
  /admin/refresh replaces (does not append) the snapshot documents; running the seed twice leaves
  1,000 customers.
```

### Scope

- All 100 rows get the block; the 63 samples flagged in this theme are the priority. Fixtures larger than 5 documents live next to the prompt (e.g. `samples/<vertical>/fixtures/<NN>-*.json`) and are linked from the block.
- The pipeline's prompt-review stage already asks the author for exactly this ("Do you want the repo to include an idempotent seed script...?", "A seed script loads sample data ... at risk") on every run; answering it once in the spreadsheet removes that question from all future runs.

## Evidence (run folders, default arm, gpt-5-mini + Agent Kit + MCP)

- runs/02-swift-message-parser-store/20261124-200226 — 02-readiness.json `information_gaps[0]` (SWIFT tag mapping absent; searched skills and Learn); audit `partly_met` on required-field validation because "required" was never defined.
- runs/15-cohort-analysis-backend/20261124-205336 — 02-readiness.json `information_gaps` (agent probed `sample_customer_360_15` via MCP, found no collections, had to guess shapes and seed size).
- runs/11-care-gap-identification-pipeline/20261124-194646 — 01-prompt-review.json `questions_for_author` and `requirements_at_risk` (seed script at risk); 02-readiness.json "Expected acceptance tests / definition of done"; 05-audit.json verdict `fail` with un-redacted seeded patient data sent to the LLM.
- runs/01-fraud-detection-with-vector-similarity/20261124-185817 vs runs/01-fraud-detection-with-vector-similarity/20261125-061803 — same prompt, incompatible seed schemas (`vector`/`pattern_name` vs `embedding`/`pattern_id`); 02-readiness.json "Fraud risk scoring formula" and "Idempotent seed script requirements".
- runs/06-order-history-timeline-agent/20261124-183612 — 02-readiness.json "Seed dataset and size / source" (searched Learn for a non-existent `sample_retail_06` seed).

## Verification

### 1. Already covered? confirmed (not covered)
- Pipeline repo: across all 100 prompt files in `samples/<vertical>/*.md`, `grep -il` finds seed 0, fixture 0, synthetic 0, "example document" 0, acceptance 0, "definition of done" 0, licen 0, upsert 3, idempotent 0, collection 6, field 17. Prompts run 47-128 words. No prompt carries a schema/seed block.
- Microsoft Learn: https://learn.microsoft.com/en-us/azure/documentdb/ (hub, updated 2026-10-08) links quickstarts, industry solution pages and RAG/agent samples, but no per-sample datasets or schemas (nothing like `sample_retail_06`); none should exist there.
- Agent Kit: `skills/local-deployment/local-sample-data-management.md` covers only the local image's built-in `sampledb` seed (`SKIP_INIT_DATA`, `INIT_DATA_PATH`) and `local-prod-parity.md` seed vs. schema scripts; neither (correctly) supplies per-sample schemas, domain references or acceptance criteria.

### 2. Premise true? confirmed (one wording fix applied)
- `loop/import_samples.py` docstring: "further rows in the Starter Prompt column are extra prompt paragraphs" and it joins `prompt_paragraphs` into the prompt file, so no importer change is needed. Confirmed.
- `loop/run-environment.md` line 9: "create the collections and indexes, load the sample data, run the queries the sample exists to show". Confirmed.
- Seed requirement wording occurs in the reference requirements (e.g. `requirements/retail-semantic-search.md`, `requirements/14-dynamic-pricing-engine.md`) and in `01-prompt-review.json` `requirements_at_risk`; `loop/draft_requirements.py` says a shared appended section requires "a seed script". The draft called this "the audit rubric"; corrected to the shared reference-requirements section the audit scores against.
- Audit counts recomputed from `runs/*/*/05-audit.json`: 115 audits with a seed-twice requirement, 72 met / 36 partly_met / 7 not_met; 11 mention `prompt_silent`. 120 readiness reports exist. Confirmed.
- banking-02 prompt quoted verbatim matches `samples/banking/02-swift-message-parser-store.md` (58 words). `sample_retail_06` appears in runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json. All cited run folders exist.
- Draft counted "upsert"/"idempotent" together as 3/100; split into upsert 3, idempotent 0.
- No Azure DocumentDB technical claims in the draft contradict the given facts (it makes no claims on vector, search, capacity or connection strings).

### 3. Maintainer skeptic: out_of_scope (for learn-docs; repo changed)
- The bucket is learn-information_gap, but nothing here is a Learn page change; the theme itself says agents "correctly found nothing" on Learn. The draft's front matter named a non-existent repo `sample-prompts-spreadsheet`.
- The ask belongs to the experiment harness, abinav2307/azure-documentdb-agent-readiness, which owns the spreadsheet import (`loop/import_samples.py`), the prompts (`samples/`), the run environment and the reference requirements. Repo changed to that one. As maintainer there I would accept it: it names the exact file path and import mechanism, gives a fixed template and two worked examples, and is specific to the DocumentDB samples gallery rather than generic hygiene.

## Finding ids

- F0014
- F0053
- F0055
- F0085
- F0159
- F0226
- F0227
- F0293
- F0327
- F0329
- F0362
- F0397
- F0434
- F0468
- F0536
- F0568
- F0642
- F0669
- F0671
- F0707
- F0708
- F0806
- F0832
- F0860
- F0863
- F0895
- F0896
- F0953
- F0982
- F1085
- F1115
- F1142
- F1210
- F1236
- F1274
- F1275
- F1765
- F1767
- F1802
- F1928
- F1964
- F1993
- F1994
- F2061
- F2096
- F2161
- F2163
- F2200
- F2225
- F2257
- F2300
- F2338
- F2370
- F2401
- F2436
- F2471
- F2494
- F2495
- F2602
- F2628
- F2755
- F2757
- F2788
- F2820
- F2853
- F2952
- F2988
- F3025
- F3050
- F3083
- F3123
- F3155
- F3190
- F3271
- F3305
- F3334
- F3371
- F3404
