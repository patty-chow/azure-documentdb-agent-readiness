---
title: "No action: integration-testing against local DocumentDB is already in the Agent Kit; LLM mocking is not DocumentDB-specific"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 2
findings: 2
bucket: learn-practice_not_public
verdicts: |
  skipped: note-only
---

# No action: testing guidance for DocumentDB and LLM mocks

**What happened:** In 2 of 100 samples (04-regulatory-reporting-orchestration and 07-customer-review-sentiment-pipeline), the audit marked two practices as prior_knowledge_only:
- Running integration tests against a real DocumentDB instance or the local gateway, for behaviour mongomock cannot emulate (indexes, explain, vector indexes, transactions).
- Stubbing OpenAI calls in CI.

**Why no change:**
1. **The kit already covers integration testing.** `skills/local-deployment/SKILL.md` documents the `documentdb-local` Gateway image on port 10260, and its `local-prod-parity` rule says to integration-test against the real container.
2. **The agent did the right thing anyway.** Sample 04 ran its unit tests on mongomock, then ran its seed and report scripts against the live cluster. Sample 07 ships a deterministic mock fallback for when no OpenAI key is set.
3. **LLM mocking is not a DocumentDB topic.** Stubbing OpenAI or embedding clients is general testing practice.

**Possible follow-up (pipeline, optional):** Check that `local-deployment` is among the skills the readiness and audit stages search, so that P24 links to it.

**Evidence:**
- runs/04-regulatory-reporting-orchestration/20261124-200545/05-audit.json, doc-gaps.md
- runs/07-customer-review-sentiment-pipeline/20261125-054042/05-audit.json, doc-gaps.md

## Verification

- skipped: note-only. As instructed, the three checks were not run.
- Skip reason: strong. The skill's description and its rule index both mention the Gateway on 10260 and the `local-prod-parity` rule ("integration-test against the real container"). I confirmed this in the kit clone at skills/local-deployment/SKILL.md, lines 3, 11 and 22. Both findings are low priority and no build was harmed.

## Finding ids

- F0692
- F1069
