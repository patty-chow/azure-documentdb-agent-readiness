---
title: "security skill: add a rule for sensitive data in AI/LLM apps (PHI/PII redaction, no secrets in prompts, app-layer authz)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 15
findings: 16
bucket: learn-practice_not_public
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# security: add `security-ai-sensitive-data` rule (PHI/PII, secrets and LLMs in generated apps)

## What happens today
`skills/security/SKILL.md` lists four rules: TLS, Private Endpoint, Entra RBAC and CMK. None of them covers what an agent-built AI app does with sensitive data on its way to and from the model.

The kit already has two related safety sections, but both govern the **agent's own behaviour**, not the code it generates:
- `skills/natural-language-querying/SKILL.md` ("Safety: Handling Sensitive Data in Sampled Documents") has a field-name and value-pattern list for redacting secrets and PII in sampled documents the agent sees.
- `skills/mcp-setup/SKILL.md` ("Safety: never receive credentials in chat") keeps the connection string out of chat, files and generated examples.

Neither skill triggers when an agent is *building* a healthcare or fintech app that sends DocumentDB documents to an LLM, and the security skill does not point to either one.

We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, gpt-5-mini, this kit plus the DocumentDB, Azure and Learn MCP servers. In **15 of 100 samples** (16 findings) the auditor marked these practices `prior_knowledge_only`, because it found no Microsoft source for them:
- Redact PHI/PII (patientId, names, account numbers, clinical text) from logs and error traces.
- Minimise or redact PII before sending text to an LLM. For PHI, use an endpoint covered by the organisation's agreements (for example an Azure OpenAI / Foundry deployment, whose data handling is described in [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)) or de-identify locally first.
- Never put a connection string or key in a prompt or tool argument. The model reaches the database only through parameterized tools.
- Persist only identifiers (conversationId, lastAppointmentId) in agent memory, not full PII-bearing context.
- Check that the caller may read this patientId or tenantId in the app layer *before* querying. Do not rely on a query filter alone.
- Say which encryption options apply. One audit suggested client-side field-level encryption (CSFLE) for PHI but found no Microsoft statement of whether it is usable on Azure DocumentDB clusters.

## Why it matters
- The clinical de-identification build added an OpenAI run mode for clinical notes with no compliance guardrail (doc-gaps.md: "PHI and external LLMs", high).
- The care-coordination audit recommended CSFLE for PHI and could not find a DocumentDB source saying whether it is supported (05-audit.json P31).
- The dynamic-pricing build kept secrets out of prompts, but had nothing to cite for doing so (doc-gaps.md: "Not sending secrets to LLMs", high).

Graders scored these checks `not_assessable`, so whether a build gets them right depends on what the model happens to know.

## Proposed change
1. New file `skills/security/security-ai-sensitive-data.md` (Category: Security, Priority: HIGH), in the existing rule format:
   - **Why it matters:** DocumentDB documents in RAG and agent apps flow into prompts, logs and agent memory.
   - **Incorrect:**
     - Interpolating the connection string, or raw documents, into the prompt.
     - `logger.info(doc)` on patient records.
     - Storing full chat transcripts that contain PII in an agent-memory collection.
     - Querying by a client-supplied patientId without checking the caller is authorized.
   - **Correct:**
     - Read the URI from env or Key Vault inside the tool (or use Entra ID / managed identity, see `security-entra-rbac`). The tool takes typed arguments (`find_patient(patient_id)`), or the app uses the DocumentDB MCP server, which holds the connection server-side.
     - One field denylist, reused from the patterns in `natural-language-querying` and extended with domain PHI fields, used by both the prompt builder and a logging filter:
       ```python
       SENSITIVE = {"patientId", "name", "dob", "ssn", "accountNumber", "clinicalNotes"}
       def redact(v):
           if isinstance(v, dict):
               return {k: ("[REDACTED]" if k in SENSITIVE else redact(x)) for k, x in v.items()}
           if isinstance(v, list):
               return [redact(x) for x in v]
           return v
       class RedactFilter(logging.Filter):
           def filter(self, r):
               if isinstance(r.args, dict): r.args = redact(r.args)
               return True
       ```
     - `authorize(user, patient_id)` before every query.
     - Identifier-only memory documents.
     - Check the LLM API key is set at startup and never log it.
   - **Encryption:** link `security-cmk-encryption` for data at rest (Learn: all data, backups and logs are AES-256 encrypted at rest, with optional CMK) and `security-entra-rbac` for identity. Add one sentence from maintainers stating whether client-side field-level encryption (explicit and automatic) and Queryable Encryption are supported on Azure DocumentDB. If they are not, say that application-level encryption of individual fields is the alternative, and that encrypted fields cannot be filtered or indexed server-side.
   - **References:** [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security), [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy).
2. `skills/security/SKILL.md`: add to Rules:
   `- [security-ai-sensitive-data](security-ai-sensitive-data.md) — Keep secrets out of prompts; redact PHI/PII from LLM calls, logs and agent memory; authorize per patient/tenant before querying.`
   Add "AI/LLM apps handling PHI or PII" to the `description` so the skill triggers for these prompts.

Out of scope for this rule: generic endpoint hygiene (rate limits, feature flags on LLM routes). It came up in a few samples but has no DocumentDB angle.

## Evidence (run folders)
- `runs/09-clinical-notes-de-identification/20261124-194349` (doc-gaps.md: "PHI and external LLMs", high)
- `runs/19-care-coordination-multi-agent/20261124-195730` (05-audit.json P31: "PHI and logging", CSFLE suggested, not_assessable)
- `runs/14-dynamic-pricing-engine/20261124-184622` (doc-gaps.md: "Not sending secrets to LLMs", high)
- `runs/01-patient-record-summarizer-rag/20261124-192917` (PHI logging, app-layer authorization)
- `runs/02-transaction-categorization-agent/20261124-190028` (PII before LLM)

## Verification

### 1. Already covered? partially_covered
- `skills/security/SKILL.md` lists only TLS, Private Endpoint, Entra RBAC and CMK rules. No rule covers LLM data flows, PHI logging, agent memory or app-layer authorization. The CMK rule says nothing about client-side field-level encryption.
- `skills/natural-language-querying/SKILL.md` does cover redaction, but for the agent itself: "The agent MUST treat any value returned by `sample_documents`, `find_documents`, or `aggregate` as untrusted and potentially sensitive." It does not apply to generated application code.
- `skills/mcp-setup/SKILL.md` covers credentials in chat ("Never ask the user to paste a connection string, password, or token into the chat"), again agent behaviour only.
- Learn https://learn.microsoft.com/en-us/azure/documentdb/security covers network, identity, TLS, encryption at rest, backup and audit logs. It says nothing about LLMs, PII/PHI or client-side field encryption. https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features does not mention CSFLE or Queryable Encryption.
- documentdb-mcp clone: no hits for field-level encryption or CSFLE.
- Edit applied: the body now acknowledges the two existing safety sections and asks the new rule to reuse and link them.

### 2. Premise true? confirmed
- Sample count verified: the 16 finding ids map to 15 distinct samples (findings-default.json). All five evidence run folders exist; the doc-gaps.md headings and the P31 check were read and match.
- Correction applied: the care-coordination audit did not "decide between CSFLE and CMK". It suggested CSFLE and found no source on whether it is supported. The body now says that.
- Correction applied: "15 of the 100 regulated-industry samples" became "15 of 100 samples".
- Learn confirms encryption at rest: "All data, backups, logs, and temporary files are encrypted on disk using Advanced Encryption Standard (AES) 256-bit encryption", with optional CMK. Entra ID / managed identities are documented on the same page.
- The "compliant endpoint" wording now points to the Foundry/Azure OpenAI data-privacy page instead of implying a compliance status. The draft does not claim that CSFLE is or is not supported. It leaves that statement to maintainers, because no public source settles it.
- The example `redact` was shallow and missed nested documents. It is now recursive. The `embedding` field was dropped from the denylist because the vector has to reach the index.

### 3. Maintainer skeptic: confirmed (with small edits)
- It names exact files (`skills/security/security-ai-sensitive-data.md`, `skills/security/SKILL.md`), follows the kit's rule format and has a concrete DocumentDB angle: the DocumentDB MCP server as the parameterized path, Entra/CMK cross-links, and a CSFLE support statement only maintainers can make.
- Edit applied: generic endpoint hygiene (rate limits, feature flags, deterministic fallbacks) was removed from the rule's scope. A maintainer would push back on it as non-DocumentDB.
- The theme was tagged learn-docs, but a skill rule is where builder agents look. A Learn note on CSFLE support on the security page would still be a useful follow-up.

## Finding ids
F0100, F0103, F0344, F0720, F0755, F1125, F1252, F1333, F1396, F1549, F1619, F1782, F2178, F2381, F2739, F3169
