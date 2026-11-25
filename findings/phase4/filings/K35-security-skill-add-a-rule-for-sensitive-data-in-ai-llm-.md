---
id: K35
title: "security skill: add a rule for sensitive data in AI/LLM applications (PHI/PII redaction, no secrets in prompts, app-layer authorization)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 15
member_drafts:
  - 122-security-and-compliance-practices-for-ai-applications-on-azu.md
open_questions: 3
---

# security skill: add a rule for sensitive data in AI/LLM applications (PHI/PII redaction, no secrets in prompts, app-layer authorization)

## What happens today

`skills/security/SKILL.md` lists four rules: TLS, Private Endpoint, Entra RBAC and CMK. None of them covers what an AI application that an agent builds does with sensitive data on its way to and from the model: prompts, logs, agent memory and per-user authorization.

The kit already has two related safety sections, but both govern the agent's own behaviour, not the code it generates:

- `skills/natural-language-querying/SKILL.md` ("Safety: Handling Sensitive Data in Sampled Documents") lists field names and value patterns for redacting secrets and PII in documents the agent itself samples.
- `skills/mcp-setup/SKILL.md` ("Safety: never receive credentials in chat") keeps the connection string out of chat, files and generated examples.

Neither triggers when an agent is building a healthcare or fintech app that sends DocumentDB documents to an LLM, and the security skill links to neither. The Learn page [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security) covers network, identity, TLS, encryption at rest, backup and audit logs, but says nothing about LLM data flows or client-side field-level encryption.

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, built by gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers loaded. In **15 of the 100 samples** (16 findings) the auditor marked these practices "prior knowledge only", because it found no Microsoft source to cite:

- Redact PHI/PII (patient ids, names, account numbers, clinical text) from logs and error traces.
- Minimise or redact PII before sending text to an LLM; for PHI, use an endpoint covered by the organisation's agreements or de-identify locally first.
- Never put a connection string or key in a prompt or tool argument; the model reaches the database only through parameterized tools.
- Persist only identifiers in agent memory, not full PII-bearing context.
- Check that the caller may read a given patient or tenant in the app layer before querying, instead of relying on a query filter alone.

Concretely: a clinical de-identification build added an OpenAI run mode for clinical notes with no compliance guardrail; a care-coordination audit recommended client-side field-level encryption (CSFLE) for PHI and could not find any source saying whether DocumentDB supports it; a dynamic-pricing build did keep secrets out of prompts but had nothing to cite. Graders scored these checks "not assessable", so whether a build gets them right depends on what the model happens to know.

Counts come from one experiment run and may shift on a re-run.

## Proposed change

**1. New file `skills/security/security-ai-sensitive-data.md`**

````markdown
# security-ai-sensitive-data

**Category:** Security · **Priority:** HIGH

## Why it matters

In RAG and agent applications, DocumentDB documents flow into prompts, logs and agent-memory collections. Regulated fields (PHI, PII, account data) and connection secrets can leak through any of these paths even when the cluster itself is locked down.

## Incorrect

- Interpolating the connection string, or raw documents, into an LLM prompt or tool argument.
- `logger.info(doc)` on patient or customer records.
- Storing full chat transcripts that contain PII in an agent-memory collection.
- Querying by a client-supplied `patientId` or `tenantId` without checking that the caller is allowed to read it.

## Correct

- Read the connection URI from an environment variable or Azure Key Vault inside the tool, or use Microsoft Entra ID / managed identity (see [security-entra-rbac](security-entra-rbac.md)). The model calls typed tools such as `find_patient(patient_id)`, or the app uses the DocumentDB MCP server, which holds the connection server-side.
- Keep one field denylist, built from the patterns in `natural-language-querying` and extended with domain fields, and use it in both the prompt builder and a logging filter:

  ```python
  import logging

  SENSITIVE = {"patientId", "name", "dob", "ssn", "accountNumber", "clinicalNotes"}

  def redact(v):
      if isinstance(v, dict):
          return {k: ("[REDACTED]" if k in SENSITIVE else redact(x)) for k, x in v.items()}
      if isinstance(v, list):
          return [redact(x) for x in v]
      return v

  class RedactFilter(logging.Filter):
      def filter(self, record):
          if isinstance(record.args, dict):
              record.args = redact(record.args)
          return True
  ```

  Do not add vector fields (for example `embedding`) to the denylist; the vector must reach the `cosmosSearch` index.
- Call `authorize(user, patient_id)` before every query that takes a caller-supplied identifier.
- Store only identifiers (for example `conversationId`, `lastAppointmentId`) in agent-memory documents.
- Minimise or de-identify text before it reaches the model. For PHI, send it only to an endpoint covered by your organisation's agreements, for example an Azure OpenAI / Foundry deployment (see [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)).
- Check at startup that the LLM API key is set, and never log it.

## Encryption

Azure DocumentDB encrypts all data, backups and logs at rest with AES-256; use [security-cmk-encryption](security-cmk-encryption.md) when you must control the key, and [security-entra-rbac](security-entra-rbac.md) for identity.
<!-- MAINTAINERS: add one sentence stating whether client-side field-level encryption (explicit and automatic) and Queryable Encryption are supported on Azure DocumentDB. If not: "Use application-level encryption of individual fields instead; encrypted fields cannot be filtered or indexed server-side." -->

## References

- [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security)
- [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)
````

**2. `skills/security/SKILL.md`**

Add to `## Rules`:

```markdown
- [security-ai-sensitive-data](security-ai-sensitive-data.md) — Keep secrets out of prompts; redact PHI/PII from LLM calls, logs and agent memory; authorize per patient/tenant before querying.
```

In the front-matter `description`, insert `, and handling PHI/PII in AI/LLM applications built on DocumentDB` right after "customer-managed keys (CMK) for encryption at rest" (before the period that precedes "Use when"), and add `building AI/LLM apps that handle PHI or PII` to its "Use when" list, so the skill triggers for these prompts.

Out of scope: generic LLM endpoint hygiene (rate limits, feature flags, fallbacks). It came up in a few samples but has no DocumentDB angle.

## Evidence

Run folders in the experiment harness:

- `runs/09-clinical-notes-de-identification/20261124-194349` (doc-gaps.md: "PHI and external LLMs", high)
- `runs/19-care-coordination-multi-agent/20261124-195730` (05-audit.json P31: PHI and logging; CSFLE suggested, not assessable)
- `runs/14-dynamic-pricing-engine/20261124-184622` (doc-gaps.md: "Not sending secrets to LLMs", high)
- `runs/01-patient-record-summarizer-rag/20261124-192917` (PHI logging, app-layer authorization)
- `runs/02-transaction-categorization-agent/20261124-190028` (PII before LLM)

## Open questions

1. [needs SME confirmation] Are client-side field-level encryption (explicit and automatic) and Queryable Encryption supported on Azure DocumentDB? No public Learn page or `documentdb-mcp` source says either way, and the rule leaves a placeholder for the engineering answer rather than asserting one.
2. [needs SME confirmation] Is pointing to an Azure OpenAI / Foundry deployment for PHI acceptable wording? The rule cites the Foundry data-privacy page but deliberately makes no compliance claim (for example HIPAA coverage); please confirm with the responsible team before merge.
3. [needs SME confirmation] Should a short note on CSFLE support also go on the Learn [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security) page, so builders outside the kit get the same answer?

## Source drafts

- 122-security-and-compliance-practices-for-ai-applications-on-azu.md
