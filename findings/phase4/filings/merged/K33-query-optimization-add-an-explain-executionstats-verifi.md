---
id: K33
title: "query-optimization: add an explain('executionStats') verification template and observability rules"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 26
member_drafts:
  - 100-samples-never-verify-plans-or-expose-operations-no-explain-e.md
open_questions: 3
---

# query-optimization: add an explain('executionStats') verification template and observability rules

## What happens today

`skills/query-optimization/query-explain-plan.md` ends with "Automate in CI with a small harness that asserts `totalDocsExamined / nReturned < threshold` for critical queries", but the kit ships no such harness and no `templates/` folder. `skills/monitoring/` covers only cluster-side setup (diagnostic settings, a Kusto query, a Bicep alert sketch); it says nothing about what the application should emit and gives agents no README text to drop into a sample. Two details in the existing monitoring rules are also wrong: the Bicep sketch uses `cpu_percent` instead of `CpuPercent`, and the slow-query rule uses a placeholder `DocumentDBSlowQueries_CL` table instead of `VCoreMongoRequests`. The kit links the MongoDB explain page but not the Azure DocumentDB pages on explain output and diagnostic logs.

## Why it matters

We had a coding agent (gpt-5-mini with this kit and the DocumentDB MCP server) build 100 Azure DocumentDB sample apps, then audited each one. Counts below are from one experiment run (latest run per sample):

| Signal | Samples |
|---|---|
| Code contains an `explain(...)` call | 2 |
| Emits OpenTelemetry / Prometheus / App Insights metrics | 0 |
| README mentions diagnostic settings, Log Analytics or slow-operation analysis | 1 |
| Agent called `documentdb_explain_operation` via MCP during the build | 11 |

The audit flagged missing plan verification or observability in 26 distinct samples (35 checks). The agent does check plans interactively, then ships nothing: in one run it called `documentdb_explain_operation` four times on the main aggregation and delivered an app with no explain step, metrics or monitoring notes. Developers who clone such a sample learn "create an index and hope it is used"; an ESR compound or cosmosSearch vector index the planner skips stays invisible until production. Agents copy template files far more reliably than they build a harness from a one-line hint. Several audits also asked for RU/s or request-charge logging, which is Cosmos DB RU vocabulary; Azure DocumentDB capacity is vCore tiers, so the new rules should say so explicitly.

## Proposed change

**1. `skills/query-optimization/query-explain-plan.md`**: replace the closing "Automate in CI..." sentence with:

```markdown
## Ship the check with the app

Do not leave explain() in your MCP session. Every sample or service must include
`scripts/explain_queries.{py,js}` (copy from `templates/`), listing its hot
find/aggregate operations. The script prints, per operation: the plan stages,
totalKeysExamined, totalDocsExamined, nReturned, executionTimeMillis and the
index name, and exits non-zero with `--strict` on COLLSCAN, an in-memory SORT,
or totalDocsExamined/nReturned > 10.
For aggregate pipelines the explain output carries a `stages` array; check the
first stage for COLLSCAN vs IXSCAN to confirm the leading $match uses an index.
Run it after seeding and after every index change; add a README step
"Verify indexes: `python scripts/explain_queries.py --strict`" and, where there
is CI, run it against the local DocumentDB container.
Optional: honour `DOCUMENTDB_EXPLAIN=1` in the app to log the plan of each hot
query once at startup (never log filter values that contain customer data).
```

Add the reference https://learn.microsoft.com/azure/documentdb/how-to-read-explain-output next to the MongoDB link.

**2. `skills/query-optimization/templates/explain_queries.py` (new)**: a pymongo script that reads the URI from `DOCUMENTDB_URI` (never printed), runs `db.command({"explain": cmd, "verbosity": "executionStats"})` for each entry in an editable `OPERATIONS` list of find/sort and aggregate operations, recursively walks the output (aggregate explain nests plans under `stages`) collecting every `stage`, `indexName`, `nReturned`, `totalKeysExamined`, `totalDocsExamined` and `executionTimeMillis`, prints one line per operation, and exits 1 under `--strict` (ratio overridable with `--ratio`) on COLLSCAN, SORT or a docs/returned ratio above the threshold. The full script is in the source draft and is pasted into this PR unchanged. `explain_queries.js` is the same shape with the Node driver. Both are tested in `testing/` against the local container the kit already uses.

**3. `skills/monitoring/SKILL.md`**: add two rules:

```markdown
- [monitoring-app-instrumentation](monitoring-app-instrumentation.md) — Emit app-side counters/latency (OpenTelemetry) for writes, retries, duplicate keys, embedding failures and slow operations; Azure DocumentDB has no request-unit or request-charge model.
- [monitoring-readme-checklist](monitoring-readme-checklist.md) — Every sample README carries an "Observability / Production checklist" section (metrics to watch, diagnostic settings to Log Analytics, slow-operation query, one alert).
```

**4. `skills/monitoring/monitoring-app-instrumentation.md` (new)**, in the kit's Why / Incorrect / Correct / References format:
- OpenTelemetry (to Azure Monitor via `azure-monitor-opentelemetry` / `@azure/monitor-opentelemetry`, or Prometheus): `db_write_total{op,outcome}`, `db_write_retries_total`, `db_duplicate_key_total`, a `db_op_duration_ms` histogram per hot operation, `embedding_failures_total`, `slow_op_total` (e.g. 500 ms) with a correlation id.
- Incorrect: `print("done")` progress output and reading a `requestCharge` field. Correct: a short Python snippet with these counters around `insert_many` and the main aggregation.
- Capacity is the vCore tier, not request units; watch cluster metrics (CpuPercent, MemoryPercent, StoragePercent, IOPS, connections) in Azure Monitor instead of computing "RU consumption".
- App-side timings matter most on M30-and-lower and free tiers, where diagnostic logs are unavailable.
- Never log connection strings, credentials or raw customer filter values.

**5. `skills/monitoring/monitoring-readme-checklist.md` (new)**: the section agents paste into READMEs:

```markdown
## Observability / Production checklist

- **Metrics**: platform metrics are collected automatically. In Azure Monitor for the
  `Microsoft.DocumentDB/mongoClusters` resource watch CpuPercent, MemoryPercent,
  StoragePercent and IOPS per node, plus connection counts (thresholds in
  `documentdb-monitoring`). There is no request-unit / request-charge metric on this service.
- **Diagnostic logs** (M40 and above; not available on M30 or lower or free tier): create a
  diagnostic setting that routes the `vCoreMongoRequests` category to Log Analytics —
  `az monitor diagnostic-settings create --name ddb-diag --resource <cluster-resource-id>
  --workspace <log-analytics-id> --logs '[{"category":"vCoreMongoRequests","enabled":true}]'`.
  Find slow operations by querying the `VCoreMongoRequests` table on `DurationMs`
  (for example P99 by `OperationName`). The table holds full command text, so restrict workspace access.
- **Verify plans**: `python scripts/explain_queries.py --strict` after seeding and after any index change.
- **Alert**: at least one metric alert (CpuPercent > 75 for 10 min) routed to your on-call channel; see
  `monitoring-metrics-alerts` for a Bicep sketch.
```

**6. Fix existing rules (same PR)**:
- `skills/monitoring/monitoring-metrics-alerts.md`: `metricName: 'cpu_percent'` → `'CpuPercent'`, and use `MemoryPercent`, `StoragePercent` and `IOPS` for any further alerts. Add the M30-and-lower caveat only where it applies (diagnostic logs, not platform metrics).
- `skills/monitoring/monitoring-slow-query-log.md`: replace `DocumentDBSlowQueries_CL` and its `DocsExamined` / `QueryShape` columns with `VCoreMongoRequests` (`DurationMs`, `OperationName`, `ErrorCode`); say there is no separate slow-query toggle (filter `vCoreMongoRequests` on duration, then confirm with explain); state the M30-and-lower / free-tier limit; link https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs instead of the landing page.

## Evidence

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json` (two violated explain/slow-query checks; `events.jsonl` shows list-indexes, no explain)
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/events.jsonl` (four interactive explain calls, nothing shipped)
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/05-audit.json` (auditor proposes `scripts/explain_queries.py`)
- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json` (asks for commit/failure, duplicate-key and retry counters)
- `runs/20-interest-accrual-batch-processor/20261124-202826/05-audit.json` (asks for a `--profile` explain flag)
- `runs/01-anti-money-laundering-pattern-detector/20261125-064030/app/src/db.py` and `runs/retail-semantic-search/20261122-152144/app/scripts/verify-live.js` (the two samples that got it right)

## Open questions

1. [needs SME confirmation] Does the template's walker match real Azure DocumentDB explain output for find, aggregate (`stages` array) and a cosmosSearch vector pipeline, including the stage names it flags (COLLSCAN, SORT)?
2. [needs SME confirmation] Should the rules say anything about throttling errors? The review flagged the claim that error 16500 / HTTP 429 "is not returned" as unconfirmed, so this PR only states there is no request-unit or request-charge model and makes no claim about 429/16500. Engineering answer requested before adding either position.
3. [needs SME confirmation] Confirm the monitoring facts used: diagnostic logs unavailable on M30-and-lower and free tiers, the `vCoreMongoRequests` category / `VCoreMongoRequests` table and columns, and metric names `CpuPercent`, `MemoryPercent`, `StoragePercent`, `IOPS`. These were checked against Learn but should be confirmed before the rules ship.

Sample counts come from a single experiment run and may shift on a re-run.

Follow-up outside this repo (not part of this PR): the experiment harness (`abinav2307/azure-documentdb-agent-readiness`) should list `scripts/explain_queries.*` and the README checklist as required deliverables and stop asking for RU/request-charge logging. That repository belongs to a colleague; coordinate that filing with them.

## Source drafts

- 100-samples-never-verify-plans-or-expose-operations-no-explain-e.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
