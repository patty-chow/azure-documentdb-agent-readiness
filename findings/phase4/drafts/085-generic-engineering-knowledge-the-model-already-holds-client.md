---
title: "No doc change: seven \"doc gaps\" are generic engineering knowledge, not Azure DocumentDB documentation (optional harness filter)"
repo: abinav2307/azure-documentdb-agent-readiness
type: note-only
status: drop
priority: P3
sample_count: 5
findings: 7
bucket: learn-doc_gap
verdicts:
  skipped: note-only
---

# Note: seven "doc gaps" are generic engineering knowledge

**Recommendation: no issue or PR against Microsoft Learn, Azure/documentdb-agent-kit or microsoft/documentdb-mcp.**

Seven audit-stage doc_gap findings across 5 of 100 samples ask for content that is not specific to Azure DocumentDB: a FAISS/hnswlib client-side ANN fallback, token-budget RAG context assembly and LLM/token-budget guidance, a sample PDF with a pdfminer.six script, an XBRL/JSON regulatory filing schema, a "prevent overlapping time ranges" booking pattern, and lat/lon clamping plus a radius cap for geo endpoints. The auditor tagged them `prior_knowledge_only` / `not_assessable` and the doc-gaps generator promoted them to `[learn_doc]` requests.

The ANN-fallback ask is harmful if forwarded: server-side cosmosSearch indexes (vector-ivf, vector-hnsw, vector-diskann) were available; `documentdb_create_index` failed only because MCP management tools were disabled (ENABLE_MANAGEMENT_TOOLS opt-in), which another theme covers. The token-budget miss was recorded by the auditor as `cause: builder_error`.

Optional (harness only): do not render checks with `availability == "prior_knowledge_only"` and no service-specific `source_url` as doc-gap entries in `doc-gaps.md`; list them under a "generic practice (no doc gap)" heading or drop them.

## Verification

- skipped: note-only. Checks (covered / premise / maintainer) were not run per stage instructions.
- Skip reason assessed as strong: all asks are generic application engineering with no DocumentDB dependency; the one service-adjacent case traces to an MCP opt-in already handled elsewhere. Status: drop.

## Finding ids

- F0233
- F0574
- F0578
- F0579
- F0677
- F0713
- F3513
