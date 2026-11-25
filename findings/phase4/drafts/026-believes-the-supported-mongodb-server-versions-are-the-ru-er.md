---
title: "azure-deployment/connection/driver skills: state the serverVersion choice (5.0/6.0/7.0/8.0) and add a one-line 'read the cluster's version' step"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 52
findings: 55
bucket: confusion-Q10
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# State the `serverVersion` choice (5.0 / 6.0 / 7.0 / 8.0) and add a one-line "read the cluster's version" step to the connection and driver skills

## What happens today

An agent using this kit with a model whose prior comes from the request-unit era of "Azure Cosmos DB for MongoDB" has nothing in the skills to correct it. In an experiment that ran gpt-5-mini through a readiness quiz plus a full build over 100 sample prompts (kit skills + DocumentDB, Azure and Learn MCP servers), the cold answer to *"Which MongoDB wire protocol or server versions are supported?"* was graded wrong, outdated or partly wrong in **55 runs across 52 of the 100 samples**:

- **29 answers** recited the RU-based story: server versions 3.2 / 3.6 / 4.0 / 4.2 / 4.4 as an "account compatibility level", with 5.0 / 6.0 "in preview" or "in newer SKUs", and "it depends on the account".
- **26 answers** pinned the product to a single version, "the service exposes a MongoDB 7.0 wire protocol", because the test cluster in the run environment happened to be 7.0.

None of this is a Learn gap. Learn already publishes the range (overview, `at-a-glance#mongodb-compatibility`, `compatibility-query-language` per-version columns) and the grounded answers found it every time. It is a training-data prior, and the kit is the lever that loads in every session. Today the kit is silent:

- `skills/azure-deployment/SKILL.md:157` — `| MongoDB server version | `8.0` | |` with an empty Notes cell and no allowed-values set.
- `skills/azure-deployment/references/bicep-cluster-template.md:54-55` — `param serverVersion string = '8.0'` with no `@allowed`, unlike `haTargetMode` right above it.
- `skills/azure-deployment/references/terraform-cluster-template.md:91-93` — `variable "mongo_version"` defaults to `"8.0"` with no `validation` block, unlike `high_availability_mode` right above it.
- `skills/connection/SKILL.md` and `skills/driver/SKILL.md` (loaded in every build) never mention wire versions or how to read a cluster's `serverVersion`.

## Why it matters

The belief leaked into builds. In **16 of the 55 runs** the build stage logged a driver-pin decision justified by the single-version belief, for example:

- `mongodb` npm pinned to `^5.7.0` "compatible with Node 24 and MongoDB 7.0 wire protocol" (04-customer-journey-mapper, 12-abandoned-cart-recovery-orchestration, 02-transaction-categorization-agent).
- `pymongo>=4.3,<5` because "PyMongo 4.x supports MongoDB 7.0 wire protocol" (10-wealth-management-rag-portal, 09-crypto-wallet-activity-analyzer, 13-chronic-disease-risk-predictor).
- Mongoose 7.x chosen for "the MongoDB 7.0 wire protocol" (03-core-banking-transaction-ledger, 03-portfolio-tracker-with-live-alerts).

These are not crashes, but they are the wrong reasoning: the agent treats one cluster's `serverVersion` as a product constraint, pins drivers backwards to match it, and (per the readiness build-risk notes) avoids newer aggregation operators it believes are "not in 4.x". A sample built this way will not run unchanged against a customer's 8.0 cluster without someone re-deriving the version story. The 3.x/4.x levels never existed on this service.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md` — parameter table (line 157)

Replace the row with:

```
| MongoDB server version | `8.0` | Allowed: `5.0`, `6.0`, `7.0`, `8.0` (default `8.0`). Set per cluster at create time (a cluster can later be upgraded to a newer major version; it is not an account-wide level). This is **not** the RU-based Azure Cosmos DB for MongoDB; its 3.2–4.4 "compatibility levels" do not exist here. Read an existing cluster's value with `az resource show -g <rg> -n <cluster> --resource-type Microsoft.DocumentDB/mongoClusters --query properties.serverVersion` (or run `az documentdb mongocluster show -g <rg> -n <cluster>` with the extension and read `serverVersion` from the output). |
```

### 2. `skills/azure-deployment/references/bicep-cluster-template.md` (lines 54-55)

```bicep
@description('MongoDB wire-protocol server version. Allowed: 5.0, 6.0, 7.0, 8.0.')
@allowed([
  '5.0'
  '6.0'
  '7.0'
  '8.0'
])
param serverVersion string = '8.0'
```

### 3. `skills/azure-deployment/references/terraform-cluster-template.md` (lines 91-93)

```hcl
variable "mongo_version" {
  type        = string
  description = "MongoDB wire-protocol server version. Allowed: 5.0, 6.0, 7.0, 8.0."
  default     = "8.0"
  validation {
    condition     = contains(["5.0", "6.0", "7.0", "8.0"], var.mongo_version)
    error_message = "serverVersion must be one of 5.0, 6.0, 7.0, 8.0."
  }
}
```

### 4. `skills/connection/SKILL.md` — new subsection after "### Authentication" (after line 75)

```markdown
### Server version

Each Azure DocumentDB cluster has its own `serverVersion`: `5.0`, `6.0`, `7.0` or `8.0`, set at create time and upgradable later. There is no account-wide "compatibility level", and the 3.x/4.x versions of the request-unit based Cosmos DB for MongoDB do not apply.

Before relying on a version-gated operator or stage, read the version from the cluster you are actually connecting to:

- `az resource show ... --query properties.serverVersion` (resource), or
- at runtime: `db.version()` / `db.adminCommand({ buildInfo: 1 }).version`, or `client.server_info()["version"]` in PyMongo (`hello.maxWireVersion` returns an integer wire version, not the "7.0"-style string).

Then check the operator in the per-version columns of
[MongoDB Query Language compatibility](https://learn.microsoft.com/azure/documentdb/compatibility-query-language).
Do not infer the product's supported range from one cluster's version.
```

### 5. `skills/driver/SKILL.md` — second rule, plus new file `skills/driver/driver-check-server-version.md`

Add to the Rules list:

```markdown
- [driver-check-server-version](driver-check-server-version.md) — Pick the current stable driver release; do not pin a driver backwards to "match" a cluster's `serverVersion`. Read the cluster's version at startup when you need version-gated features.
```

`driver-check-server-version.md` in the existing rule format (Category: Driver Best Practices, Priority: MEDIUM): *Why it matters* — every current official driver (Node `mongodb` 6.x, PyMongo 4.x, Java 5.x, Go 2.x, .NET 3.x) speaks wire versions 5.0 through 8.0, so there is nothing to gain by pinning to an older line "for 7.0"; *Incorrect* — `"mongodb": "^5.7.0"  // "because the cluster is MongoDB 7.0"`; *Correct* — current stable driver + a startup log of `hello.maxWireVersion` / `server_info()["version"]`; *References* — `compatibility-query-language`, `at-a-glance#mongodb-compatibility`.

## Evidence (run folders from the experiment; no connection strings)

- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json` — `confusions[Q10]`, outcome **wrong**: cold answer lists 3.2/3.6/4.0, "4.2/5.0 in some regions".
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` — `confusions[Q10]`, outcome **wrong**: "compatibility up to MongoDB 4.x/5.0".
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` — `confusions[Q10]`, outcome **outdated**: 3.6/4.0/4.2, "depends on account serverVersion setting".
- `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json` (Q10) and `01-prompt-review.md:50-51` — single-version belief ("advertises MongoDB 7.0 wire protocol") carried into the driver choice.
- `runs/04-customer-journey-mapper/20261124-203553/events.jsonl` — build-stage `log_decision`: `mongodb ^5.7.0` "compatible with ... MongoDB 7.0 wire protocol".
- `runs/10-wealth-management-rag-portal/20261124-201449/events.jsonl` — build-stage `log_decision`: `pymongo>=4.3,<5` "supports MongoDB 7.0 wire protocol".

Side note for the experiment harness (not this PR): the readiness run-environment note describes the test cluster as "MongoDB 7.0 wire protocol"; labelling it "this cluster's serverVersion" would stop the model generalising it into a product fact.

## Verification

### 1. Already covered? — confirmed (not in the target)

The Agent Kit clone does not state the allowed server versions or how to read a cluster's version:
- `skills/azure-deployment/SKILL.md:157`: `| MongoDB server version | `8.0` | |` (empty Notes cell, no allowed set).
- `skills/azure-deployment/references/bicep-cluster-template.md:54-55`: `@description('MongoDB wire-protocol server version.')` / `param serverVersion string = '8.0'`, no `@allowed`, while `haTargetMode` directly above has one.
- `skills/azure-deployment/references/terraform-cluster-template.md:91-93`: `variable "mongo_version"` with `default = "8.0"` and no `validation` block, while `high_availability_mode` directly above has one.
- `skills/connection/SKILL.md` ("Azure DocumentDB Connection Specifics" covers connection string format, TLS, authentication only) and `skills/driver/SKILL.md` (single rule `driver-singleton-client`) contain no occurrence of `serverVersion`, wire version, `buildInfo` or `maxWireVersion` (grep over `skills/` and `knowledge-base/`). Other hits are only hard-coded `serverVersion: '8.0'` in examples (`storage-choose-premium-ssdv2.md:48`, `ha-enable-for-production.md:60`).
- microsoft/documentdb-mcp clone: no `serverVersion` / wire-version guidance either (not the target).
Learn already documents the range, which is why the draft correctly does not ask for a Learn change: https://learn.microsoft.com/en-us/azure/documentdb/overview ("supports MongoDB wire protocol versions 5.0 through 8.0") and https://learn.microsoft.com/en-us/azure/documentdb/at-a-glance ("supports MongoDB wire protocol versions 5.0, 6.0, 7.0, and 8.0").

### 2. Premise true? — confirmed (with small precision edits applied)

- Supported versions 5.0/6.0/7.0/8.0: confirmed by the overview and at-a-glance pages above and by https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language (per-version columns v5.0, v6.0, v7.0, v8.0; `buildInfo` and `hello` supported in all four).
- RU-based Cosmos DB for MongoDB is a separate service: at-a-glance "Naming" states "Azure DocumentDB and Azure Cosmos DB for MongoDB (RU) are separate services", and that it was previously named vCore-based Azure Cosmos DB for MongoDB. So 3.2-4.4 "compatibility levels" do not apply.
- Resource type `Microsoft.DocumentDB/mongoClusters` and CLI group `az documentdb mongocluster`: consistent with the stated facts and the kit's own Bicep (`Microsoft.DocumentDB/mongoClusters@2025-09-01`).
- Edits applied to the body: (a) "chosen at create time" softened to "set at create time and upgradable later", since a cluster's major version is not fixed for life; (b) the extension CLI example no longer asserts an exact JMESPath (`--query serverVersion`), and says to read `serverVersion` from the `show` output, keeping the verified `az resource show ... --query properties.serverVersion` form; (c) the runtime check now uses `db.version()` / `buildInfo.version` / `server_info()["version"]` for the version string and notes that `hello.maxWireVersion` is an integer wire version, not "7.0".
- Driver claim (current Node 6.x, PyMongo 4.x, Java 5.x, Go 2.x, .NET 3.x drivers support MongoDB 5.0-8.0 servers): consistent with the MongoDB driver compatibility matrices; not contradicted by any Azure DocumentDB source.

### 3. Maintainer skeptic — confirmed

Names exact files and line numbers in Azure/documentdb-agent-kit, gives copy-ready replacement text that mirrors existing patterns in the same files (`@allowed` on `haTargetMode`, `validation` on `high_availability_mode`, the existing rule-file format in `skills/driver/`), and is specific to Azure DocumentDB (the RU vs vCore version confusion). The harness note is explicitly marked out of this PR. I would accept it with the small wording edits above.

## Finding ids

- F0008
- F0112
- F0262
- F0319
- F0353
- F0460
- F0601
- F0797
- F0828
- F0851
- F0947
- F1044
- F1135
- F1165
- F1228
- F1263
- F1405
- F1491
- F1561
- F1660
- F0218
- F0499
- F0529
- F0699
- F1004
- F1592
- F1721
- F1793
- F1830
- F1894
- F1925
- F1955
- F1986
- F2056
- F2087
- F2125
- F2156
- F2189
- F2220
- F2247
- F2292
- F2329
- F2392
- F2429
- F2750
- F2845
- F2879
- F2944
- F2979
- F3017
- F3045
- F3114
- F3180
- F3301
- F3502
