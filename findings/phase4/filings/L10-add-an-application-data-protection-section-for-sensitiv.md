---
id: L10
title: "Add an application data protection section for sensitive data and LLM pipelines"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 20
member_drafts:
  - 079-sensitive-data-and-llm-in-the-loop-governance-on-azure-docum.md
open_questions: 2
---

# Add an application data protection section for sensitive data and LLM pipelines

Target: Learn, Azure DocumentDB > Security (https://learn.microsoft.com/en-us/azure/documentdb/security), plus one new how-to.

## What happens today

The Security page covers only infrastructure controls (network, identity, transport, encryption, backup, monitoring). Nothing tells an application builder what to do with regulated data (PII/PHI) or with data sent to an LLM:

- that a `{ patientId }` or `{ tenantId }` filter is not authorization: the app must map the authenticated identity to allowed ids before it queries;
- how to keep identifiers out of what an agent or prompt reads (projections) and out of application logs;
- how to record LLM-made decisions as history with provenance instead of overwriting fields;
- how long agent memory holding identifiers should live, and how TTL indexes behave on Azure DocumentDB.

Learn also has no Azure DocumentDB TTL page: the indexing page has no TTL section, the compatibility page only lists the TTL index property as supported, the only statement of the purge behaviour is a 2025-10-10 release note, and search returns the request-unit-based Azure Cosmos DB for MongoDB `_ts` TTL page, which does not apply to vCore clusters. The Security page's Data encryption section covers only encryption at rest and TLS. Client-side field-level encryption appears only as a "Yes" with an empty Notes cell in the compare-mongodb-atlas Security and compliance table and in a 2025-10-10 [Preview] release note on schema enforcement with CSFLE, with no how-to; no Azure DocumentDB Learn page mentions Queryable Encryption, HIPAA, PHI or LLM data flows.

## Why it matters

In an experiment where a coding agent built 100 sample applications on Azure DocumentDB, 20 of the 100 samples (24 audit findings) hit this gap: the agent found no Learn page for these practices and skipped them or improvised. Counts are from one experiment run with known harness issues. Examples:

- A care-gap pipeline put whole patient records into the LLM prompt unredacted.
- A customer-lifetime-value pipeline wrote LLM JSON straight into customer documents with `$set`, with no enum or range check, overwriting the previous score instead of keeping history.
- A patient-record RAG app relied on a `patientId` pre-filter as its only access control and logged without redaction.
- A prescription-refill agent stored the last medication in agent memory with no TTL index and no retention note.
- A dedupe pipeline deleted merged documents with no merge record and matched un-canonicalized e-mails.
- Others sent account text or medication lists to external models, read full documents instead of projecting, or could send the same notification twice.

## Proposed change

Keep it Azure DocumentDB-specific; link out to Learn "Data, privacy, and security for Foundry Models sold by Azure" (https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy) and the Azure compliance offerings (for example https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us) instead of restating them, and make no HIPAA or BAA coverage claim for Azure DocumentDB or Azure OpenAI.

**1. `azure/documentdb/security.md`**: add an "Application data protection" section with four bullets, each linking to the new how-to:

- An application-layer authorization check is required on top of data-plane RBAC and secondary users. A `{ patientId }` or `{ tenantId }` filter is a safeguard, not authorization.
- Read with projections so agents and LLM prompts get only the fields they need. Keep identifiers and clinical or free text out of logs and external model calls; minimize or de-identify first.
- Record LLM-made decisions as append-only history (`$push`) with provenance, not as overwrites.
- Put a TTL index on short-lived agent memory and session data.

Also add one sentence to the existing Data encryption section: explicit client-side field-level encryption (CSFLE) is listed as supported (compare-mongodb-atlas, Security and compliance table; release notes 2025-10-10 "[Preview] Add schema enforcement with CSFLE (client side field level encryption) integration"), automatic CSFLE is not documented, and Queryable Encryption is not supported (the engine rejects `encryptedFields` with CommandNotSupported "encryptedFields not supported yet", `pg_documentdb/src/commands/create_collection_view.c:526-529`).

**2. New how-to "Protect sensitive data in applications and AI pipelines"** (suggested `azure/documentdb/how-to-protect-sensitive-data-ai.md`, `ms.topic: how-to`, under Security in `toc.yml`). Code first, one screen per section:

1. **Authorize in the app before you query**: a minimal Express or FastAPI middleware that resolves the Microsoft Entra ID token to allowed tenant or patient ids and rejects the request before any `find`. Cross-link `how-to-connect-role-based-access-control` and `secondary-users`.
2. **Minimal projections and redacted logging**: `find(filter, { projection: { items: 1, total: 1, _id: 0 } })`; log `_id` and field names, never values; a short `redact`/`hashId` helper for Node and Python.
3. **Before an external model call**: reduce to aggregates or pseudonymized fields; gate raw-document mode behind an opt-in environment variable that is off by default; show one acceptable and one unacceptable payload. For PHI, point to an endpoint covered by the reader's own agreements and link the Foundry data-privacy page (prompts, completions and embeddings are not available to other customers or to OpenAI and are not used to train foundation models without permission); do not assert compliance coverage.
4. **Validate model output before a write**: check enums, numeric ranges and string lengths in application code; send low-confidence or malformed results to a quarantine collection. One pydantic and one zod example. State that collection-level `$jsonSchema` validators (`validator`, `validationLevel`, `validationAction`) are a gated preview on Azure DocumentDB (release notes 2025-10-10) with no enablement step on Learn, and return CommandNotSupported "validator not supported yet" until enabled (`pg_documentdb/src/metadata/collection.c:2270-2277`); when enabled they apply to insert, update, findAndModify and `$merge`/`$out` (compatibility page). The `$jsonSchema` reference lists `enum`, `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties` and `dependencies` as unsupported, so a validator example must use `bsonType`, `required`, `pattern`, `minimum`/`maximum`, `minLength`/`maxLength` and an `$in` query for enumerations, not `enum`. Application-side validation stays the primary check.
5. **Provenance and history instead of overwrite**: a subdocument `{ model, modelVersion, promptHash, score, tier, rationale, schemaVersion, createdAt }` (`createdAt` as a UTC BSON Date) appended with `$push` (optionally `$each` + `$slice` to cap length); an append-only notification log with a unique index on an idempotency key such as `{ cartId: 1, templateId: 1, sendWindow: 1 }`; a `merge_history` document for dedupe merges.
6. **Canonical identifiers**: normalize e-mail (lowercase, trim) and phone numbers (E.164) before hashing; store and index the hash as the equality key.
7. **Retention for agent memory (TTL)**: link the new TTL section of the indexing page (item 4 below) and show the pattern:
   - the indexed field must be a BSON `Date`; the purger deletes with a Date-typed `$lt` predicate, so numbers, strings and missing fields are never deleted (an inference from the engine source, `pg_documentdb/src/ttl/ttl_index.c` lines 603-760);
   - TTL requires a single-field index: the engine rejects compound indexes with "TTL indexes work only on single fields, and compound indexes are incompatible with TTL functionality." (`pg_documentdb/src/commands/create_indexes.c:2793`), and `expireAfterSeconds` must be numeric;
   - `expireAfterSeconds: 0` with an explicit `expiresAt` field deletes at a set time;
   - expiry lags by up to about a minute and is not exact: the TTL task is scheduled every minute and runs batch deletions continuously for up to 60 seconds (release notes 2025-10-10, "[Preview]"; engine `background_job_configs.c` lines 79-124). In this experiment a document with `expireAfterSeconds: 0` and a Date 5 s in the future was still present after 30 s;
   - a `partialFilterExpression` on the index also limits what the TTL purge deletes;
   - verify with `listIndexes`, then `countDocuments` after the delay;
   - store canonical ids in memory, not clinical text.

**3. Callouts**: add one line to the vector-search/RAG how-to and the Node and Python quickstarts: "Before you put real customer or patient data in this sample, see Protect sensitive data in applications and AI pipelines."

**4. `azure/documentdb/indexing.md`**: add a TTL section (`expireAfterSeconds`, Date-only field, single-field only, "lags by up to about a minute") so the how-to and the kit have a Learn page to cite; today the only Learn statement of the purge behaviour is the 2025-10-10 release note, and Learn search lands on the RU-based Azure Cosmos DB for MongoDB `_ts` page.

Follow-up (separate PR, Azure/documentdb-agent-kit): add a fifth, application-layer rule to `skills/security/SKILL.md` mirroring sections 2.1 and 2.2 and linking `skills/indexing/index-ttl-expiry.md`. Coordinate with the kit security-skill PRs K03/K35 (which add the CSFLE/QE and PHI statements) so only one PR adds this rule, and with the kit fix that changes `index-ttl-expiry.md` and `index-pattern-cookbook.md` from "roughly every 60 seconds" to "lags by up to about a minute" and cites the release note and engine source instead of MongoDB docs only.

## Evidence

Run folders in the experiment repository:

- `runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.json` (check P28)
- `runs/12-clv-prediction-pipeline/20261124-204841/05-audit.json` (checks P15, P16)
- `runs/01-patient-record-summarizer-rag/20261124-192917/doc-gaps.md`
- `runs/15-prescription-refill-agent/20261124-195253/05-audit.json` (check P69)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/doc-gaps.md`
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/events.jsonl` (TTL delete not observed within 30 s of a 5 s expiry; observation)

Other samples with the same gap (15, for 20 in total): 02-transaction-categorization-agent, 03-medication-interaction-checker, 08-insurance-pre-auth-multi-agent, 08-personalized-email-campaign-builder, 09-clinical-notes-de-identification, 12-abandoned-cart-recovery-orchestration, 12-invoice-matching-reconciliation, 13-basel-iii-capital-ratio-calculator, 16-multi-touch-attribution-model, 16-subscription-billing-engine, 17-seasonal-trend-spotter-agent, 17-stress-testing-multi-agent-runner, 18-adverse-event-reporting-pipeline, 18-chargeback-dispute-multi-agent, 18-returns-refund-workflow-orchestration.

## Resolved

- Collection-level `$jsonSchema` validators and `enum`: validators are a gated preview on Azure DocumentDB that returns CommandNotSupported "validator not supported yet" until enabled, with no enablement step documented on Learn, and the `$jsonSchema` reference lists `enum`, `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties` and `dependencies` as unsupported (the engine main branch parses `enum` and `oneOf` since July 2026 but the service does not document them), so the how-to keeps application-side validation primary and uses `pattern`/`$in` rather than `enum`. Sources: https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema; https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language; https://learn.microsoft.com/en-us/azure/documentdb/release-notes (2025-10-10); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/jsonschema/bson_json_schema_tree.c; https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/metadata/collection.c (lines 2270-2277).
- TTL semantics (single-field only, Date-only, lag): the engine rejects compound TTL indexes and non-numeric `expireAfterSeconds`, the purger deletes with a Date-typed `$lt` predicate so non-Date and missing values are not deleted (inference from source), and expiry lags by up to about a minute because the task runs every minute with batch deletions for up to 60 seconds; the filing's wording "roughly every 60 seconds" was replaced by "lags by up to about a minute, not exact". Sources: https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/create_indexes.c (lines 2289-2303, 2789-2793); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/ttl/ttl_index.c (lines 603-760); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/configs/background_job_configs.c (lines 79-124); https://learn.microsoft.com/en-us/azure/documentdb/release-notes (October 10, 2025); `runs/12-hospital-bed-occupancy-tracker/20261124-194835/events.jsonl`.
- CSFLE and Queryable Encryption statement for the Security page: explicit CSFLE is listed as supported with no how-to, automatic CSFLE is undocumented, and Queryable Encryption is not supported because the engine rejects `encryptedFields`. Sources: https://learn.microsoft.com/en-us/azure/documentdb/compare-mongodb-atlas; https://learn.microsoft.com/en-us/azure/documentdb/release-notes (October 10, 2025); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/create_collection_view.c (lines 526-529).
- Facts for the external-model guidance: Learn's Foundry data-privacy page states prompts, completions and embeddings are not available to other customers or to OpenAI and are not used to train foundation models without permission; Microsoft's HIPAA page says BAA coverage comes via the Product Terms for in-scope services and does not by itself make a customer compliant; no Azure DocumentDB Learn page mentions HIPAA, PHI or LLM data flows. Sources: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy; https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us; https://learn.microsoft.com/en-us/azure/documentdb/security.

## Open questions

1. [needs SME confirmation] Actual TTL purge cadence on managed clusters: the every-minute schedule with up-to-60-second continuous batches is the open-source engine default and the release note marks the continuous behaviour as [Preview]; service-side values are not published and the one observation (no delete within 30 s of a 5 s expiry) does not bound the lag. The filing says "lags by up to about a minute, not exact" until engineering confirms.
2. The 20-of-100 count (24 finding ids) comes from one run with known harness issues; re-run after the harness fixes or confirm before quoting it publicly.

## Source drafts

- 079-sensitive-data-and-llm-in-the-loop-governance-on-azure-docum.md
