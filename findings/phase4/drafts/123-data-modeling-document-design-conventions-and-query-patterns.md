---
title: "data-modeling skill: add rules for monetary values, BSON Date/UTC, and immutable audit/provenance records"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 16
findings: 21
bucket: learn-practice_not_public
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# data-modeling: add rules for money, dates, and immutable audit/provenance records

## What happens today
`skills/data-modeling/SKILL.md` has five rules: embed-vs-reference, the 16 MB limit, denormalization, `schemaVersion`, and large-field split. None of them covers **which BSON type to use for a field**, or **how to model records that must never change** (ledgers, audit trails, merge history). One rule elsewhere in the kit works against the ledger case: `skills/indexing/index-ttl-expiry.md` lists "short-lived audit logs" as a good TTL use case and never warns against TTL on ledgers or compliance audit trails.

We ran 100 Azure DocumentDB sample prompts through gpt-5-mini with this kit loaded. In **16 samples** (21 findings), the audit stage marked modeling decisions as `prior_knowledge_only`, meaning the agent had no DocumentDB source to cite:
- **Money.** It recommended Decimal128 or integer minor units over JS `Number`. In 07-multi-currency-ledger the builder listed `amount` but never typed it as Decimal128.
- **Dates.** It recommended storing temporal fields as BSON `Date` in UTC (17-seasonal-trend-spotter).
- **Ledgers.** It recommended no TTL index on an immutable ledger, and read-only `createdAt` / `createdBy` / `transactionRef` fields (03-core-banking).
- **Provenance.** It recommended keeping merge history in a separate collection instead of deleting the originals, and saving scores plus model/prompt version with LLM-assisted merges (18-cdp, 17-stress-testing).
- **Query support.** In 13-algorithmic-trade-journal the agent could not confirm that `$setWindowFields` or `$jsonSchema` validators work on Azure DocumentDB. It computed drawdown in the client and skipped validation. Both are in fact listed as supported on the Learn MQL compatibility page, but nothing in the kit points the agent there, so it never found that page.

## Proposed change
Add three rule files using the existing format (why it matters, incorrect, correct, references), and list them in `SKILL.md`:

1. **`model-monetary-values.md`** (HIGH)
   - Store money as `Decimal128` (`NumberDecimal("12.34")` in mongosh, `mongoose.Schema.Types.Decimal128` in a Mongoose schema, `bson.Decimal128` in PyMongo) or as integer minor units plus a `currency` code.
   - Use `$toDecimal` before `$multiply` / `$divide` in aggregations (`$toDecimal` is listed as supported on the Learn MQL compatibility page).
   - Incorrect example: `{ amount: 12.34 }` stored as a double.

2. **`model-dates-bson-utc.md`** (MEDIUM)
   - Store timestamps as BSON `Date` (always UTC), never as strings or local time. A TTL index also only expires `Date` values (link to `index-ttl-expiry.md`).
   - Query with explicit `$gte` / `$lt` ranges. Use `$dateTrunc` / `$dateToParts` with a `timezone` argument to bucket by local time when reading.
   - Index the date field. In compound indexes, put the date after the equality fields (ESR order, see `skills/indexing`).

3. **`model-immutable-audit-records.md`** (MEDIUM)
   - Ledger and audit collections are append-only, with `createdAt`, `createdBy`, a source reference and `schemaVersion`.
   - Never put a TTL index on them. Put expiring data in a separate collection. Also add a one-line caveat to `skills/indexing/index-ttl-expiry.md`: TTL suits short-lived operational logs, not ledgers or compliance audit trails.
   - Corrections are new compensating entries, not updates.
   - For merges or LLM-assisted decisions, write a provenance document (`run_id`, inputs, scores, model and prompt version, `created_at`) to its own collection and keep or soft-delete the originals.
   - Optionally enforce required fields and types with a collection `$jsonSchema` validator. Learn lists `$jsonSchema` and schema validation on insert, update, findAndModify and `$merge` / `$out` as supported.

Also update the `description:` front matter to mention "field types for money and time, immutable ledgers and audit trails" so the skill gets loaded for ledger, finance and audit prompts.

**Follow-up in `skills/query-optimization/`:** add a short rule saying that `$setWindowFields` (with window operators such as `$sum` and `$max`) and `$jsonSchema` are supported on Azure DocumentDB versions 5.0 to 8.0. Cite https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language and give one example pipeline (cumulative sum and running max for drawdown). Only `allowDiskUse` behaviour needs maintainer confirmation, because the compatibility page does not mention it.

## Evidence (run folders)
- runs/07-multi-currency-ledger/20261124-190814 (doc-gaps.md: "Decimal128 / currency arithmetic guidance")
- runs/03-core-banking-transaction-ledger/20261124-200452 (doc-gaps.md: "avoid TTL on transaction/ledger collections")
- runs/13-algorithmic-trade-journal/20261124-191835 (doc-gaps.md: "setWindowFields availability", JSON Schema validator)
- runs/18-360-data-platform-cdp-orchestration/20261124-205822 (05-audit.json: merge provenance, model/prompt metadata)
- runs/17-seasonal-trend-spotter-agent/20261124-185115 (05-audit.json: BSON Date in UTC)

## Verification

### 1. Already covered? confirmed (not there)
- `skills/data-modeling/SKILL.md` lists only model-embed-vs-reference, model-16mb-limit, model-denormalize-reads, model-schema-versioning and model-large-field-split. Its description covers "embed vs reference, 16 MB document limit, denormalization for read-heavy workloads, schema versioning". Searching `skills/` and `knowledge-base/` for Decimal128, NumberDecimal, ledger, provenance, immutable, setWindowFields, jsonSchema and allowDiskUse finds no rule on these topics.
- `skills/indexing/index-ttl-expiry.md` says the TTL field "must be a `Date`", but it lists "short-lived audit logs" as a TTL use case with no ledger caveat. That partly conflicts with the proposed rule, so the draft now includes a small edit to it.
- `skills/query-optimization/` holds only SKILL.md and query-explain-plan.md, with no operator-support rule.
- Schema versioning (F0065, F3170) is already covered by `model-schema-versioning.md`. The theme's other topics (structured tags, shard-key explanation, dedicated database) are not part of this PR.

### 2. Premise true? confirmed (one sub-claim corrected)
- The main premise is true. The kit has no field-type or immutable-record rules, and in 16 distinct samples (21 findings in findings-default.json, all `practice_not_public`) the audit recorded these items as `prior_knowledge_only`. Example: F1154 in 07-multi-currency-ledger 05-audit.json says "Store monetary amounts using Decimal128 or integer minor-units". The quoted doc-gaps.md headings exist in the cited run folders.
- Corrected sub-claim: the original draft asked maintainers to confirm support for `$setWindowFields` and `$jsonSchema`. That support is already public. https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language lists `$setWindowFields` as supported for v5.0 to 8.0, `$jsonSchema*` as supported, and `$toDecimal`, `$dateTrunc` and the window operators as supported. It also says "Schema validation supports: insert, update, findAndModify, and the $merge / $out stages". The body now cites this page and leaves only `allowDiskUse` open, since the page does not mention it.
- Corrected sub-claim: the Mongoose schema type is `mongoose.Schema.Types.Decimal128`. `mongoose.Types.Decimal128` is the value constructor.
- BSON Date values are always stored as UTC milliseconds, so the UTC rule is accurate. The draft makes no claim that conflicts with the fixed service facts (resource type, CLI group, connection string, vCore tiers).

### 3. Maintainer skeptic: confirmed
- The draft names exact files (three new files under `skills/data-modeling/`, SKILL.md front matter, a one-line edit to `skills/indexing/index-ttl-expiry.md`, and a new rule in `skills/query-optimization/`) and follows the existing rule format. The kit already has general MongoDB-practice rules (for example, model-schema-versioning cites "MongoDB Schema Versioning pattern"), so the scope fits.
- The rules have a DocumentDB angle: they link to the Learn compatibility page for Decimal128 / `$toDecimal`, `$jsonSchema` validation and `$setWindowFields`, and they fix a TTL guidance gap in the kit itself. I would accept this as a PR after the small edits above.

## Finding ids
F0065, F0243, F0373, F0382, F0383, F0721, F1068, F1154, F1428, F1781, F2115, F2143, F2144, F2145, F2447, F2773, F2936, F2969, F3004, F3005, F3170
