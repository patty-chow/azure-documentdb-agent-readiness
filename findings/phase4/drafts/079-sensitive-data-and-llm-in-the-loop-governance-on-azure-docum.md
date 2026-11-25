---
title: "Learn docs: add an \"Application data protection\" section (and short how-to) for sensitive data and LLM pipelines under Azure DocumentDB > Security"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 20
findings: 24
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add application data protection guidance for sensitive data and LLM pipelines to the Azure DocumentDB Security section

## What happens today

The Security best-practices page (https://learn.microsoft.com/en-us/azure/documentdb/security, source `azure/documentdb/security.md` in MicrosoftDocs/nosql-docs-pr) has sections for Network security, Identity management, Transport security, Data encryption, Backup and restore, and Monitoring and response. All of them are infrastructure controls. Nothing in the section says what the application has to do with regulated data (PHI/PII) or with data sent to an LLM:

- that a `patientId`/tenant filter in a query is not authorization: the app must map the authenticated identity to the ids it may read before it queries, on top of data-plane RBAC and secondary users,
- how to keep identifiers out of what an agent reads (projections) and out of application logs,
- how to record provenance and history for LLM-made decisions instead of overwriting fields,
- how long agent memory that holds identifiers should live (TTL), and how TTL behaves on Azure DocumentDB.

Learn has no Azure DocumentDB page on TTL indexes either. The indexing concepts page (https://learn.microsoft.com/en-us/azure/documentdb/indexing) covers single-field, compound, partial, text, wildcard and geospatial indexes but not TTL. The only TTL page that search returns is the request-unit-based Azure Cosmos DB for MongoDB page (https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/time-to-live), which does not apply to vCore clusters.

In Azure/documentdb-agent-kit, the `documentdb-security` skill (`skills/security/SKILL.md`) has only four rules: TLS, Private Endpoint, Entra RBAC and CMK. None of them is an application-layer rule. The kit does have two related pieces. `skills/natural-language-querying/SKILL.md` tells the agent itself to redact PII it reads through MCP tools, but it does not cover the code the agent writes. `skills/indexing/index-ttl-expiry.md` gives the TTL semantics. Neither is linked from the security skill.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini, DocumentDB Agent Kit, DocumentDB/Azure/Learn MCP servers), 20 of the 100 samples (24 audit findings) hit this gap. The auditor logged the practice as `prior_knowledge_only` or `violated` because it could not cite any Learn page or kit rule. What this caused in the generated code:

- **Care-gap pipeline**: `agent.py` puts whole patient records, contact details included, into the LLM prompt whenever an API key is set. Nothing is redacted (`runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.json`, check P28).
- **CLV pipeline**: LLM JSON is cast and written straight into customer documents with `$set`, with no enum or range check. `clv_score`/`clv_tier`/`clv_rationale` are overwritten instead of being added to a history array (`runs/12-clv-prediction-pipeline/20261124-204841/05-audit.json`, checks P15 and P16, both `violated`).
- **Patient-record RAG**: the only access control is a `patientId` pre-filter, with no authentication or authorization layer, and the sample logs without redaction (`runs/01-patient-record-summarizer-rag/20261124-192917/doc-gaps.md`).
- **Prescription-refill agent**: agent memory in the database stores `lastMedication` with no TTL index and no retention note (`runs/15-prescription-refill-agent/20261124-195253/05-audit.json`, check P69).
- **CDP dedupe**: merged customer documents are deleted with no `merge_history` record and no model or prompt metadata, and e-mails are not canonicalized before matching (`runs/18-360-data-platform-cdp-orchestration/20261124-205822/doc-gaps.md`).
- **Other samples**: fintech and healthcare samples sent merchant/account text or medication lists to external models and logged errors without redaction. The Basel III sample sent only aggregates, but by the builder's own instinct. The abandoned-cart sample had no append-only notification log and could send the same message twice. The returns workflow read full order documents instead of projecting the fields it needed.

## Proposed change

Keep the change DocumentDB-specific and link out for generic compliance and AI-privacy guidance. Learn already has that guidance, for example Azure OpenAI "Data, privacy, and security" and the HIPAA/BAA compliance offerings. Don't restate it.

**1. Security page (`azure/documentdb/security.md`)**: add an "Application data protection" section with four bullets, each linking to the new how-to:

- An application-layer authorization check is required on top of data-plane RBAC and secondary users. A `{ patientId }` or `{ tenantId }` query filter is a safeguard, not authorization.
- Read with projections so that agents and LLM prompts get only the fields they need. Keep identifiers and clinical or free text out of application logs and out of external model calls, and minimize or de-identify data first (link to the Azure OpenAI data, privacy and security page).
- Record LLM-made decisions as append-only history (`$push`) with provenance, not as overwrites.
- Put a TTL index on short-lived agent memory and session data.

**2. New how-to "Protect sensitive data in applications and AI pipelines"** (suggested source `azure/documentdb/how-to-protect-sensitive-data-ai.md`, `ms.topic: how-to`, added to the Security node of `toc.yml`). Put code first and keep each section to one screen:

1. **Authorize in the app before you query.** Show a minimal Express or FastAPI middleware that resolves the Microsoft Entra ID token to the set of allowed tenant or patient ids and rejects the request before any `find`. Cross-link to the data-plane RBAC (`how-to-connect-role-based-access-control`) and secondary users (`secondary-users`) pages for the database side of least privilege.
2. **Minimal projections and redacted logging.** Show `find(filter, { projection: { items: 1, total: 1, _id: 0 } })`. Log the document `_id` and the list of fields, never their values. Include a short `redact`/`hashId` helper for Node and Python.
3. **Before an external model call.** Reduce the data to aggregates or pseudonymized fields. Gate raw-document mode behind an opt-in environment variable that is off by default. Show one acceptable payload and one unacceptable payload. Link out to the Azure OpenAI data-privacy and compliance pages; don't write a compliance checklist here.
4. **Validate model output before a write.** Check enums, numeric ranges and string lengths. Write low-confidence or malformed results to a quarantine collection, not to the source-of-truth document. Give one short Python (pydantic) example and one Node (zod) example. A collection-level `$jsonSchema` validator can be mentioned as an extra layer only if it is confirmed as supported on Azure DocumentDB.
5. **Provenance and history instead of overwrite.**
   - Use a subdocument `{ model, modelVersion, promptHash, score, tier, rationale, schemaVersion, createdAt }`, with `createdAt` stored as a BSON Date in UTC.
   - Append it with `$push` (optionally with `$each` and `$slice` to cap the array length) instead of using `$set` on top-level fields.
   - Keep an append-only notification log with a unique index on an idempotency key (for example `{ cartId: 1, templateId: 1, sendWindow: 1 }`) so a message can't go out twice.
   - Write a `merge_history` document for dedupe merges.
6. **Canonical identifiers.** Normalize e-mail (lowercase, trim) and phone numbers (E.164) before hashing. Store the hash as the equality key and index it.
7. **Retention for agent memory (TTL).** This page, or a new TTL section on the indexing page, has to state the semantics itself, because no Azure DocumentDB TTL page exists on Learn to link to:
   - The indexed field must be a BSON `Date`; documents with non-Date values never expire.
   - The index must be a single-field index. A compound index can't be a TTL index.
   - Use `expireAfterSeconds: 0` with an explicit `expiresAt` field to delete at a set time.
   - A background task deletes expired documents about every 60 seconds, so expiry isn't exact to the second.
   - To verify: insert a document with an `expiresAt` slightly in the future, confirm the index with `listIndexes`, then check `countDocuments` after the deletion delay, not right away.
   - Store canonical ids in memory documents, not medication or clinical text.

**3. Callouts**: add a one-line note to the vector-search/RAG how-to and the Node/Python quickstarts: "Before you put real customer or patient data in this sample, see Protect sensitive data in applications and AI pipelines."

A separate PR to Azure/documentdb-agent-kit should add a fifth rule to `skills/security/SKILL.md` that mirrors section 2.1 and 2.2 (app-layer authorization, projections, redacted logging) and links to `skills/indexing/index-ttl-expiry.md`.

## Evidence (run folders under azure-documentdb-agent-readiness/runs)

- `runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.json`: whole patient records go into the LLM prompt with no redaction (P28, prior_knowledge_only).
- `runs/12-clv-prediction-pipeline/20261124-204841/05-audit.json`: unvalidated LLM output is written with `$set` and no history is kept (P15 and P16, violated).
- `runs/01-patient-record-summarizer-rag/20261124-192917/doc-gaps.md`: gaps in PHI logging and app-layer authorization.
- `runs/15-prescription-refill-agent/20261124-195253/05-audit.json`: agent memory has no TTL index and no retention note (P69, violated).
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/doc-gaps.md`: no merge provenance, no model or prompt metadata, no canonical ids.

Other samples with the same gap: 02-transaction-categorization-agent, 03-medication-interaction-checker, 08-insurance-pre-auth-multi-agent, 08-personalized-email-campaign-builder, 09-clinical-notes-de-identification, 12-abandoned-cart-recovery-orchestration, 12-invoice-matching-reconciliation, 13-basel-iii-capital-ratio-calculator, 16-multi-touch-attribution-model, 16-subscription-billing-engine, 17-seasonal-trend-spotter-agent, 17-stress-testing-multi-agent-runner, 18-adverse-event-reporting-pipeline, 18-chargeback-dispute-multi-agent, 18-returns-refund-workflow-orchestration.

## Verification

### 1. Already covered? partially_covered

- **Learn Security page**: confirmed missing. https://learn.microsoft.com/en-us/azure/documentdb/security (ms.date 2025-09-29) has only these sections: Network security, Identity management, Transport security, Data encryption, Backup and restore, Monitoring and response. It never mentions PII/PHI, redaction, application-layer authorization, LLM or AI data handling, projections, history or TTL. The closest text is "Use native data plane role-based access control to query, create, and access items", which is database-side least privilege, not application authorization.
- **Learn TTL guidance**: missing. https://learn.microsoft.com/en-us/azure/documentdb/indexing has no TTL section, https://learn.microsoft.com/en-us/azure/documentdb/ttl returns 404, and Learn search returns only the Cosmos DB for MongoDB RU page (https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/time-to-live).
- **Agent kit, partial**:
  - `skills/security/SKILL.md` lists only the TLS, Private Endpoint, Entra RBAC and CMK rules.
  - `skills/natural-language-querying/SKILL.md` covers redaction only for values the agent itself reads through MCP: "Collections frequently hold ... PII (emails, phone numbers, SSNs, payment data)" and "Never echo raw sample documents back to the user." It doesn't apply to the application code the agent writes.
  - `skills/indexing/index-ttl-expiry.md` gives the TTL semantics ("A background thread deletes expired documents roughly every 60 seconds"; "The indexed field must be a Date"). The security skill doesn't link to it.

### 2. Premise true? confirmed (one claim corrected)

- Confirmed: the Security section's coverage matches the draft's description (fetched page above).
- Confirmed: the kit's security skill has exactly four infrastructure rules.
- Corrected: the original draft said to "link to the existing TTL guidance" on Learn for the ~60 s deletion delay. No such Azure DocumentDB Learn page exists, so the body now asks the page to state the TTL semantics itself. The source for those semantics is the kit's `index-ttl-expiry.md`; the RU-based Cosmos DB for MongoDB TTL page does not apply.
- `$push` with `$each`/`$slice`, single-field TTL with a BSON Date field, `expireAfterSeconds: 0` with an `expiresAt` field, projections and unique indexes are all standard MongoDB-compatible features that Azure DocumentDB supports. The draft makes no claims about resource type, connection string, vector or capacity. `$jsonSchema` validator support was not verified, so the body mentions it only conditionally.

### 3. Maintainer skeptic: confirmed (with scope edits)

The original draft read partly as generic engineering hygiene: PHI definitions, logging-library setup, a compliance checklist with BAA items. A Learn maintainer would push back on those because Azure OpenAI and Azure compliance docs already own them. The edited body ties every item to a named page and file (`security.md`, a new `how-to-protect-sensitive-data-ai.md`, `toc.yml`, quickstart and RAG callouts) and to Azure DocumentDB features: data-plane RBAC and secondary users, projections, `$push` history, unique idempotency indexes, and TTL indexes, for which Learn has no page today. Generic compliance content is now link-out only. The TTL semantics fill a real gap in the DocumentDB docs. As edited, it is an acceptable Learn feedback item for MicrosoftDocs/nosql-docs-pr, with a follow-up PR to Azure/documentdb-agent-kit `skills/security/SKILL.md`.

## Finding ids

F0092, F0094, F0340, F0407, F1240, F1315, F1387, F1770, F1969, F2000, F2001, F2107, F2167, F2609, F2733, F2798, F2926, F2966, F2994, F2995, F2996, F3028, F3060, F3094
