---
title: "Multi-tenant isolation pattern (tenantId-enforcing Mongoose plugin + isolation tests): no action"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 1
findings: 2
bucket: learn-practice_not_public
verdicts:
  skipped: note-only
---

# Note: multi-tenant tenantId enforcement pattern (no action)

**What happened.** In 1 of 100 samples (10-multi-tenant-storefront-saas), the audit tagged two practices as `prior_knowledge_only`, meaning no public DocumentDB source was cited:
- K01: inject or require `{ tenantId }` on every read and write through a central Mongoose plugin or repository layer.
- K19: tests that fail when `updateMany`/`deleteMany` or a read runs without `tenantId`.

**Outcome.** The audit marked both practices `followed`. The app has `app/src/models/tenantSafetyPlugin.js` and `tests/isolation.test.js`. The cold-quiz answer to S04 (how tenant isolation is enforced in the repository layer) was `correct`, and grounding confirmed it against the Learn Mongoose tutorial.

**Why no action.** The agent's prior knowledge was correct and it applied it. This is generic MongoDB/Mongoose application practice, not DocumentDB-specific behavior. It comes from one sample at low priority.

**Possible later work.** A future "Multi-tenancy on Azure DocumentDB" page, if planned, should cover service-level choices (database-per-tenant vs. shared collection, `tenantId` as shard key and leading index key, Entra ID/RBAC scoping); the plugin-and-test pattern could be a short appendix.

**Evidence**
- runs/10-multi-tenant-storefront-saas/20261124-184121/05-audit.json (checks K01, K19)
- runs/10-multi-tenant-storefront-saas/20261124-184121/02-readiness.json (confusion S04, outcome correct)
- runs/10-multi-tenant-storefront-saas/20261124-184121/doc-gaps.md
- runs/10-multi-tenant-storefront-saas/20261124-184121/app/src/models/tenantSafetyPlugin.js

## Verification

- skipped: note-only. Checks not run per stage instructions.
- Skip reason (accepted as strong): S04 scored correct in the cold quiz and both practices were followed in the build. The pattern is generic Mongoose/MongoDB practice, not DocumentDB-specific, and came from 1 sample at low priority, so no Learn page or kit change is justified.

## Finding ids

- F1677
- F1678
