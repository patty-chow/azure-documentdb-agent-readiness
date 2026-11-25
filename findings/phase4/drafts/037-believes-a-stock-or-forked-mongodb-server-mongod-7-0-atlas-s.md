---
title: "Note only: cold-quiz 'stock MongoDB server underneath' prior is already corrected by Learn, the Agent Kit and grounding"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 13
findings: 13
bucket: confusion-Q15
verdicts:
  skipped: note-only
---

## Note

In 13 of 100 samples the cold (ungrounded) answer to readiness question Q15 assumed Azure DocumentDB runs a hosted upstream MongoDB server (mongod / WiredTiger / "MongoDB 7.0-compatible engine") or a Microsoft fork. The driver conclusion (use standard MongoDB drivers) was right; the risk was relying on server admin commands, Atlas recipes or Atlas Search / Atlas Vector Search syntax.

What is true: Azure DocumentDB does not run the MongoDB server codebase; it is the PostgreSQL-based DocumentDB engine (github.com/documentdb/documentdb) implementing the MongoDB wire protocol. Vector search uses cosmosSearch indexes (vector-ivf, vector-hnsw, vector-diskann); full-text search uses DocumentDB text/search indexes, not Atlas Search.

## Skip reason

Already covered: the Learn overview states the service does not run the MongoDB database server or its codebase, the Learn compatibility pages list supported operators and commands, and the Agent Kit AGENTS.md plus the vector-search and full-text-search skills call out cosmosSearch and search-index differences from community MongoDB. Grounded answers corrected the prior and audits showed no admin-command or Atlas-syntax defects. The one sub-ask (F3330, list differing admin commands in the driver skill) is better served by linking the existing Learn compatibility matrix. Model prior, no fix needed.

## Verification

- skipped: note-only (checks not run per stage instructions).

## Finding ids

F0221, F0503, F0533, F0665, F0702, F1596, F1868, F2129, F2598, F2848, F2947, F3184, F3330
