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
open_questions: 3
---

# Add an application data protection section for sensitive data and LLM pipelines

Target: Learn, Azure DocumentDB > Security (https://learn.microsoft.com/en-us/azure/documentdb/security), plus one new how-to.

## What happens today

The Security page covers only infrastructure controls (network, identity, transport, encryption, backup, monitoring). Nothing tells an application builder what to do with regulated data (PII/PHI) or with data sent to an LLM:

- that a `{ patientId }` or `{ tenantId }` filter is not authorization: the app must map the authenticated identity to allowed ids before it queries;
- how to keep identifiers out of what an agent or prompt reads (projections) and out of application logs;
- how to record LLM-made decisions as history with provenance instead of overwriting fields;
- how long agent memory holding identifiers should live, and how TTL indexes behave on Azure DocumentDB.

Learn also has no Azure DocumentDB TTL page: the indexing page has no TTL section, and search returns only the request-unit-based Azure Cosmos DB for MongoDB TTL page, which does not apply to vCore clusters.

## Why it matters

In an experiment where a coding agent built 100 sample applications on Azure DocumentDB, 20 of the 100 samples (24 audit findings) hit this gap: the agent found no Learn page for these practices and skipped them or improvised. Counts are from one experiment run with known harness issues [needs SME confirmation]. Examples:

- A care-gap pipeline put whole patient records into the LLM prompt unredacted.
- A customer-lifetime-value pipeline wrote LLM JSON straight into customer documents with `$set`, with no enum or range check, overwriting the previous score instead of keeping history.
- A patient-record RAG app relied on a `patientId` pre-filter as its only access control and logged without redaction.
- A prescription-refill agent stored the last medication in agent memory with no TTL index and no retention note.
- A dedupe pipeline deleted merged documents with no merge record and matched un-canonicalized e-mails.
- Others sent account text or medication lists to external models, read full documents instead of projecting, or could send the same notification twice.

## Proposed change

Keep it Azure DocumentDB-specific; link out to Azure OpenAI "Data, privacy, and security" and the compliance offerings instead of restating them.

**1. `azure/documentdb/security.md`**: add an "Application data protection" section with four bullets, each linking to the new how-to:

- An application-layer authorization check is required on top of data-plane RBAC and secondary users. A `{ patientId }` or `{ tenantId }` filter is a safeguard, not authorization.
- Read with projections so agents and LLM prompts get only the fields they need. Keep identifiers and clinical or free text out of logs and external model calls; minimize or de-identify first.
- Record LLM-made decisions as append-only history (`$push`) with provenance, not as overwrites.
- Put a TTL index on short-lived agent memory and session data.

**2. New how-to "Protect sensitive data in applications and AI pipelines"** (suggested `azure/documentdb/how-to-protect-sensitive-data-ai.md`, `ms.topic: how-to`, under Security in `toc.yml`). Code first, one screen per section:

1. **Authorize in the app before you query**: a minimal Express or FastAPI middleware that resolves the Microsoft Entra ID token to allowed tenant or patient ids and rejects the request before any `find`. Cross-link `how-to-connect-role-based-access-control` and `secondary-users`.
2. **Minimal projections and redacted logging**: `find(filter, { projection: { items: 1, total: 1, _id: 0 } })`; log `_id` and field names, never values; a short `redact`/`hashId` helper for Node and Python.
3. **Before an external model call**: reduce to aggregates or pseudonymized fields; gate raw-document mode behind an opt-in environment variable that is off by default; show one acceptable and one unacceptable payload.
4. **Validate model output before a write**: check enums, numeric ranges and string lengths; send low-confidence or malformed results to a quarantine collection. One pydantic and one zod example. Mention a collection-level `$jsonSchema` validator only if confirmed as supported [needs SME confirmation].
5. **Provenance and history instead of overwrite**: a subdocument `{ model, modelVersion, promptHash, score, tier, rationale, schemaVersion, createdAt }` (`createdAt` as a UTC BSON Date) appended with `$push` (optionally `$each` + `$slice` to cap length); an append-only notification log with a unique index on an idempotency key such as `{ cartId: 1, templateId: 1, sendWindow: 1 }`; a `merge_history` document for dedupe merges.
6. **Canonical identifiers**: normalize e-mail (lowercase, trim) and phone numbers (E.164) before hashing; store and index the hash as the equality key.
7. **Retention for agent memory (TTL)**: state the semantics here or in the indexing page (no Azure DocumentDB TTL page exists on Learn to link to) [needs SME confirmation]:
   - the indexed field must be a BSON `Date`; non-Date values never expire;
   - TTL requires a single-field index, not a compound or multikey one;
   - `expireAfterSeconds: 0` with an explicit `expiresAt` field deletes at a set time;
   - a background task deletes expired documents about every 60 seconds, so expiry is not exact;
   - verify with `listIndexes`, then `countDocuments` after the delay;
   - store canonical ids in memory, not clinical text.

**3. Callouts**: add one line to the vector-search/RAG how-to and the Node and Python quickstarts: "Before you put real customer or patient data in this sample, see Protect sensitive data in applications and AI pipelines."

Follow-up (separate PR, Azure/documentdb-agent-kit): add a fifth, application-layer rule to `skills/security/SKILL.md` mirroring sections 2.1 and 2.2 and linking `skills/indexing/index-ttl-expiry.md`. Coordinate with the kit security-skill PR from draft 122 so only one PR adds this rule.

## Evidence

Run folders in the experiment repository:

- `runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.json` (check P28)
- `runs/12-clv-prediction-pipeline/20261124-204841/05-audit.json` (checks P15, P16)
- `runs/01-patient-record-summarizer-rag/20261124-192917/doc-gaps.md`
- `runs/15-prescription-refill-agent/20261124-195253/05-audit.json` (check P69)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/doc-gaps.md`

Other samples with the same gap (15, for 20 in total): 02-transaction-categorization-agent, 03-medication-interaction-checker, 08-insurance-pre-auth-multi-agent, 08-personalized-email-campaign-builder, 09-clinical-notes-de-identification, 12-abandoned-cart-recovery-orchestration, 12-invoice-matching-reconciliation, 13-basel-iii-capital-ratio-calculator, 16-multi-touch-attribution-model, 16-subscription-billing-engine, 17-seasonal-trend-spotter-agent, 17-stress-testing-multi-agent-runner, 18-adverse-event-reporting-pipeline, 18-chargeback-dispute-multi-agent, 18-returns-refund-workflow-orchestration.

## Open questions

1. [needs SME confirmation] Is a collection-level `$jsonSchema` validator (including `enum`) supported on Azure DocumentDB? Another draft from this experiment says `enum` is unsupported; mention validators only if engineering confirms.
2. [needs SME confirmation] The TTL semantics in section 2.7 (BSON Date only, single-field only, roughly 60-second background deletion) come from the DocumentDB Agent Kit's `index-ttl-expiry.md`, not from Learn. Please confirm they hold on Azure DocumentDB before publishing.
3. [needs SME confirmation] The 20-of-100 count (24 finding ids) comes from one run with known harness issues; re-run after the harness fixes or confirm before quoting it publicly.

## Source drafts

- 079-sensitive-data-and-llm-in-the-loop-governance-on-azure-docum.md
