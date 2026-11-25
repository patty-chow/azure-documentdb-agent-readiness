---
title: "No action: generic app-engineering practices flagged prior_knowledge_only (LLM hygiene, idempotency, testing, fallbacks)"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 15
findings: 17
bucket: learn-practice_not_public
verdicts:
  skipped: note-only
---

# No action: generic app-engineering practices flagged as prior_knowledge_only

In 15 of the 100 samples, the audit stage labeled 17 practices `prior_knowledge_only` because it could not find a DocumentDB source to cite. None of them is specific to DocumentDB. They fall into four groups: LLM integration hygiene (semaphore-bounded OpenAI calls, taxonomy validation, untrusted-output quarantine, token guards with fallbacks, time normalization), reliability (webhook dedup, workflow-run status, rule caching, web-search timeouts, fallback flags), testing (driver mocks, deterministic offline embeddings), and data hygiene (TTL and version fields on agent memory, audit metadata, lat/long validation).

## Skip reason
These are general engineering and LLM-integration practices that the model already knew, not DocumentDB behavior. None contradicts DocumentDB docs, so a Learn or Agent Kit change would only add generic content. The `prior_knowledge_only` label comes from the auditor's citation requirement, so if anything needs fixing it is the harness taxonomy. Optional: add a `general_engineering` category to the audit prompt.

## Verification
Skipped: note-only. The skip reason is sound, so the status is drop.

## Finding ids
F1032, F1067, F1429, F0343, F0964, F0488, F0689, F0490, F1650, F1820, F1821, F2212, F2545, F2935, F2970, F3524, F3035
