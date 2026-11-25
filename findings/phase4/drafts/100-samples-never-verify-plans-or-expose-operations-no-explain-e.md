---
title: "Add a shippable explain('executionStats') verification template and app-observability rules to documentdb-query-optimization / documentdb-monitoring"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 26
findings: 35
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a shippable `explain('executionStats')` template and app-observability rules (query-optimization + monitoring skills)

## What happens today

`skills/query-optimization/query-explain-plan.md` ends with "Automate in CI with a small harness that asserts `totalDocsExamined / nReturned < threshold` for critical queries", but the kit ships no such harness. `skills/monitoring/` covers cluster-side setup (diagnostic settings, a Kusto query, a Bicep alert sketch) but says nothing about what the application itself should emit and gives agents no README-ready text to drop into a sample. Two details in the existing monitoring rules are also out of date with the service (see section 6).

The result, measured over 100 generated Azure DocumentDB sample apps built with gpt-5-mini plus this kit and the DocumentDB MCP server (latest run per sample):

| Signal | Count |
|---|---|
| Sample code contains an `explain(...)` call | 2 |
| Sample emits OpenTelemetry / Prometheus / App Insights metrics | 0 |
| Sample README mentions diagnostic settings, Log Analytics or slow-operation analysis | 1 |
| Builder called `documentdb_explain_operation` interactively via MCP during the build | 11 |
| Builder called `documentdb_list_indexes` interactively via MCP | 67 |

The agent knows to check plans (it does so in the MCP session) but never leaves that check in the deliverable. The audit stage flagged this as a violated practice in 35 checks across 26 distinct samples, all sourced to `documentdb-monitoring`, `documentdb-query-optimization` or `documentdb-query-optimizer`.

Typical audit evidence:

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json`: two violated checks ("Explain and slow-query logging", "Use explain() for query performance"); `events.jsonl` shows a `documentdb_list_indexes` call and no explain.
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/events.jsonl`: the builder ran `documentdb_explain_operation` four times on the wallet aggregation, then shipped an app with no explain step, no metrics and no monitoring README section.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/05-audit.json`: the auditor proposes a small `scripts/explain_queries.py` that runs explain('executionStats') for the sample queries and prints keysExamined/docsExamined.
- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json`: asks for counters for commits/failures, duplicate-key events and retry counts.
- `runs/20-interest-accrual-batch-processor/20261124-202826/05-audit.json`: asks for a `--profile` flag that runs explain and logs keysExamined/docsExamined.

Two samples got it right and show the shape is achievable: `runs/retail-semantic-search/20261122-152144/app/scripts/verify-live.js` and `runs/01-anti-money-laundering-pattern-detector/20261125-064030/app/src/db.py`.

## Why it matters

- 26 samples were explicitly flagged and almost none of the 100 ship any plan verification. Developers who clone a sample learn "create index, hope it is used". A cosmosSearch vector index or an ESR compound index that the planner does not pick stays invisible until production.
- The kit already carries the right guidance in prose; the agent fails on the last step (turning an interactive MCP check into a file in the repo). Agents copy template files far more reliably than they synthesise harnesses from a one-line hint.
- Vocabulary: many auditor check texts asked for "RU/s", "request charge" or "429 throttling" logging. That is Cosmos DB RU-based vocabulary. Azure DocumentDB is sized by M-series vCore tier and monitored through cluster metrics (CpuPercent, MemoryPercent, StoragePercent, IOPS, connections); it returns no request charge. The kit's own text is already correct; the new rules should state the negative explicitly so agents stop inventing `requestCharge` logging. (The audit rubric fix is tracked separately in the pipeline repo.)

## Proposed change

### 1. `skills/query-optimization/query-explain-plan.md`

Replace the closing sentence ("Automate in CI with a small harness...") with:

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

Also add a reference link to the Azure page, alongside the existing MongoDB one: https://learn.microsoft.com/azure/documentdb/how-to-read-explain-output

### 2. `skills/query-optimization/templates/explain_queries.py` (new)

```python
"""Verify that the app's hot queries use indexes on Azure DocumentDB.
Usage: python scripts/explain_queries.py [--strict] [--ratio 10]
Reads DOCUMENTDB_URI from the environment; never prints it."""
import json, os, sys
from pymongo import MongoClient

# Edit this list: (collection, {"find": {...}, "sort": {...}} | {"aggregate": [...]})
OPERATIONS = [
    ("orders", {"find": {"status": "shipped", "region": "US"}, "sort": {"date": -1}}),
    ("orders", {"aggregate": [{"$match": {"status": "shipped"}}, {"$group": {"_id": "$region", "n": {"$sum": 1}}}]}),
]

def explain(db, coll, op):
    if "aggregate" in op:
        cmd = {"aggregate": coll, "pipeline": op["aggregate"], "cursor": {}}
    else:
        cmd = {"find": coll, "filter": op.get("find", {})}
        if "sort" in op:
            cmd["sort"] = op["sort"]
    return db.command({"explain": cmd, "verbosity": "executionStats"})

def walk(node, stages, stats, indexes):
    # Aggregate explain nests plans and stats under a `stages` array, so search recursively.
    if isinstance(node, dict):
        if isinstance(node.get("stage"), str):
            stages.append(node["stage"])
        if "indexName" in node:
            indexes.append(node["indexName"])
        for k in ("nReturned", "totalKeysExamined", "totalDocsExamined", "executionTimeMillis"):
            if k in node and k not in stats:
                stats[k] = node[k]
        for v in node.values():
            walk(v, stages, stats, indexes)
    elif isinstance(node, list):
        for v in node:
            walk(v, stages, stats, indexes)

def main():
    strict = "--strict" in sys.argv
    ratio_max = float(sys.argv[sys.argv.index("--ratio") + 1]) if "--ratio" in sys.argv else 10.0
    client = MongoClient(os.environ["DOCUMENTDB_URI"])
    db = client[os.environ.get("DOCUMENTDB_DB", "appdb")]
    bad = 0
    for coll, op in OPERATIONS:
        stages, stats, indexes = [], {}, []
        walk(explain(db, coll, op), stages, stats, indexes)
        n = stats.get("nReturned", 0)
        docs = stats.get("totalDocsExamined", 0)
        ratio = docs / n if n else (float("inf") if docs else 0)
        warn = "COLLSCAN" in stages or "SORT" in stages or ratio > ratio_max
        bad += warn
        print(f"[{'WARN' if warn else 'ok'}] {coll} {json.dumps(op)[:80]} stages={stages} index={indexes} "
              f"keysExamined={stats.get('totalKeysExamined')} docsExamined={docs} nReturned={n} "
              f"ms={stats.get('executionTimeMillis')}")
    if strict and bad:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

`explain_queries.js` is the same shape with the Node driver (`db.command({ explain: cmd, verbosity: 'executionStats' })`). Maintainers: please validate the walker against real Azure DocumentDB explain output for find, aggregate and a cosmosSearch `$search` pipeline (the walker deliberately collects any `stage` / `indexName` key anywhere in the tree), and test both templates in `testing/` against the local container the kit already uses.

### 3. `skills/monitoring/SKILL.md`: add two rules

```markdown
- [monitoring-app-instrumentation](monitoring-app-instrumentation.md) — Emit app-side counters/latency (OpenTelemetry) for writes, retries, duplicate keys, embedding failures and slow operations; there is no request charge on Azure DocumentDB.
- [monitoring-readme-checklist](monitoring-readme-checklist.md) — Every sample README carries an "Observability / Production checklist" section (metrics to watch, diagnostic settings to Log Analytics, slow-operation query, one alert).
```

### 4. `skills/monitoring/monitoring-app-instrumentation.md` (new), key content

- Instrument with OpenTelemetry (export to Azure Monitor via `azure-monitor-opentelemetry` / `@azure/monitor-opentelemetry`, or to Prometheus): `db_write_total{op,outcome}`, `db_write_retries_total`, `db_duplicate_key_total`, a `db_op_duration_ms` histogram per hot operation, `embedding_failures_total`, `slow_op_total` (threshold e.g. 500 ms) with a correlation id in the log line.
- Incorrect example: `print("done")` progress output and a `requestCharge` field read from the response. Correct example: a 15-line Python snippet with the counters above around `insert_many` and the main aggregation.
- State plainly: Azure DocumentDB returns no request charge and has no RU/s or 429-throttling model; capacity is the M-series vCore tier. Watch cluster metrics (CpuPercent, MemoryPercent, StoragePercent, IOPS, connections) in Azure Monitor instead of computing "RU consumption" in the app.
- App-side instrumentation matters most on M30 and lower tiers and free tier, where diagnostic logs are not available, so the app's own timings are the only per-operation signal.
- Never log connection strings, credentials or raw customer filter values.

### 5. `skills/monitoring/monitoring-readme-checklist.md` (new), the paragraph agents paste into README

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

### 6. Fix two inaccuracies in the existing monitoring rules (same PR)

- `skills/monitoring/monitoring-metrics-alerts.md`: the Bicep sketch uses `metricName: 'cpu_percent'`; the supported metric for `Microsoft.DocumentDB/mongoClusters` is `CpuPercent` (likewise `MemoryPercent`, `StoragePercent`, `IOPS`). Add the M30-and-lower caveat only where it applies (diagnostic logs, not platform metrics).
- `skills/monitoring/monitoring-slow-query-log.md`: replace the placeholder `DocumentDBSlowQueries_CL` table and `DocsExamined` / `QueryShape` columns with the real resource-specific table `VCoreMongoRequests` (columns such as `DurationMs`, `OperationName`, `ErrorCode`), say there is no separate slow-query toggle (slow operations are found by filtering `vCoreMongoRequests` on duration, then confirmed with explain), and state that diagnostic logs are not available on M30 or lower tiers or free tier. Replace the generic `https://learn.microsoft.com/azure/documentdb/` reference with https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs.

### Follow-ups outside this repo (not part of this PR)

- Pipeline (`abinav2307/azure-documentdb-agent-readiness`, build prompt): list `scripts/explain_queries.*` and the README observability section as required deliverables, and have the audit rubric stop asking for RU/request-charge logging.
- Adjacent audit findings in the same bucket (`F1544` projections, `F1777` early `$match`) are query-shape issues already covered by `query-optimizer/references/`; no kit change proposed here.

## Evidence (run folders)

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json` and `events.jsonl`
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/events.jsonl` (4 interactive `documentdb_explain_operation` calls, nothing shipped)
- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json`
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/05-audit.json`
- `runs/20-interest-accrual-batch-processor/20261124-202826/05-audit.json`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? partially_covered

The kit has the guidance as prose but no deliverable artifact.
- `skills/query-optimization/query-explain-plan.md` line 26: "Automate in CI with a small harness that asserts `totalDocsExamined / nReturned < threshold` for critical queries." No harness, template or `templates/` folder exists anywhere under `skills/` (grep for `explain_queries` and `templates/` under skills returns nothing relevant).
- `skills/monitoring/SKILL.md` has only two rules (`monitoring-slow-query-log`, `monitoring-metrics-alerts`), both cluster-side. Grep of `skills/` and `knowledge-base/` for `opentelemetry`, `prometheus`, `requestCharge`, `request charge` returns no files, so app-side instrumentation and the explicit no-request-charge statement are absent.
- Learn already documents how to read explain output (https://learn.microsoft.com/en-us/azure/documentdb/how-to-read-explain-output) and diagnostic logs (https://learn.microsoft.com/en-us/azure/documentdb/how-to-monitor-diagnostics-logs), but the kit links neither; it links the MongoDB explain page and the Azure DocumentDB landing page only.

### 2. Premise true? confirmed (with corrections applied)

The core premise holds: Azure DocumentDB supports `explain("executionStats")` on find and aggregate, with `winningPlan.stage` values COLLSCAN / IXSCAN / FETCH / SORT and `nReturned`, `totalKeysExamined`, `totalDocsExamined`, `executionTimeMillis` (how-to-read-explain-output page). Corrections applied to the body:
- Diagnostic logs: "This feature is not available with compute tier `M30` or lower tiers, or free-tier SKUs" (how-to-monitor-diagnostics-logs). Added that caveat to the README checklist and instrumentation rule; the experiment's own cluster was M30, so this matters for samples.
- There is no separate "slow-query log" toggle. The log category is `vCoreMongoRequests`, queried in the resource-specific `VCoreMongoRequests` table on `DurationMs` / `OperationName` / `ErrorCode` (same page; Azure Monitor supported-logs and table reference for Microsoft.DocumentDB/mongoClusters). Replaced the `categoryGroup allLogs` + "enable the slow-query log" wording and dropped the `--metrics AllMetrics` export (platform metrics are collected automatically; DS export status varies by metric on the supported-metrics page).
- Metric names: the supported-metrics reference for Microsoft.DocumentDB/mongoClusters (https://learn.microsoft.com/azure/azure-monitor/reference/supported-metrics/microsoft-documentdb-mongoclusters-metrics) lists `CpuPercent`, `MemoryPercent`, `StoragePercent`, `IOPS`. The kit's `cpu_percent` and placeholder `DocumentDBSlowQueries_CL` are wrong; added section 6 to fix them.
- `VCoreMongoRequests` contains full command text (PiiCommandText column, table reference), so the checklist now says to restrict workspace access.
- Aggregate explain output nests plans under a `stages` array (Learn explain page); the template now walks the whole tree for stats instead of reading only top-level `executionStats`, and also flags in-memory SORT.
- RU vocabulary correction is right: Azure DocumentDB capacity is M-series vCore tiers, no request units.

### 3. Maintainer skeptic: confirmed

As a maintainer of Azure/documentdb-agent-kit I would accept this with small edits: it names the exact files (`query-explain-plan.md`, `monitoring/SKILL.md`, two new rule files, a `templates/` folder), the change is concrete, it is Azure-DocumentDB-specific (vCore metrics, vCoreMongoRequests, tier limits, no request charge), and it fixes two existing factual errors in the kit's monitoring rules. Expected review asks: run the templates in `testing/`, keep the rule files in the kit's standard Why / Incorrect / Correct / References format. The pipeline follow-ups are correctly scoped out to the pipeline repo.

## Finding ids

F0247, F0304, F0310, F0381, F0384, F0551, F1289, F1330, F1362, F1425, F1323, F1513, F1614, F1649, F1778, F1783, F1544, F1777, F1944, F1946, F1976, F2046, F2508, F2614, F2643, F2510, F2481, F2835, F2929, F3003, F3167, F3168, F3292, F3419, F3526
