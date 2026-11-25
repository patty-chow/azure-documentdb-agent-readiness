---
id: K20
title: "Document the serverVersion choice in the azure-deployment, connection and driver skills"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 52
member_drafts:
  - 026-believes-the-supported-mongodb-server-versions-are-the-ru-er.md
open_questions: 4
---

# Document the serverVersion choice in the azure-deployment, connection and driver skills

## What happens today

Nothing in the kit tells an agent which MongoDB server versions an Azure DocumentDB cluster can run, or how to read the version of the cluster it is connected to. Models trained on the older request-unit (RU) based Azure Cosmos DB for MongoDB fill the gap with that service's story, which does not apply here. Asked "Which MongoDB wire protocol or server versions are supported?" without grounding, gpt-5-mini answered in two wrong ways:

- **RU-era answer:** 3.2 / 3.6 / 4.0 / 4.2 / 4.4 as an account-wide "compatibility level", with 5.0 / 6.0 "in preview".
- **Single-version answer:** "the service exposes a MongoDB 7.0 wire protocol", generalised from the one test cluster that happened to run 7.0.

Learn already documents the range (overview, at-a-glance, and the per-version columns of the query-language compatibility page), and grounded answers found it. The gap is in the kit, which loads in every session:

- `skills/azure-deployment/SKILL.md:157`: the "MongoDB server version" row shows `8.0` with an empty Notes cell and no allowed values.
- `skills/azure-deployment/references/bicep-cluster-template.md:54-55`: `param serverVersion string = '8.0'` has no `@allowed`, unlike `haTargetMode` directly above it.
- `skills/azure-deployment/references/terraform-cluster-template.md:91-93`: `variable "mongo_version"` has no `validation` block, unlike `high_availability_mode` directly above it.
- `skills/connection/SKILL.md` and `skills/driver/SKILL.md` never mention `serverVersion`, wire versions, `buildInfo` or `maxWireVersion`.

## Why it matters

In one experiment run (100 sample app prompts, gpt-5-mini with the kit and the DocumentDB, Azure and Learn MCP servers), the cold answer was wrong, outdated or partly wrong in 55 runs across **52 of the 100 samples**. Counts are from that single run, and may move on a re-run.

The belief then reached the code. In 16 of those runs the build stage logged a driver choice justified by "the cluster is MongoDB 7.0": `mongodb` npm pinned to `^5.7.0`, `pymongo>=4.3,<5`, or Mongoose 7.x picked "for the 7.0 wire protocol". The agent treats one cluster's version as a product limit, pins drivers backwards to match it, and avoids operators it thinks are "not in 4.x". The 3.x/4.x levels never existed on this service.

## Proposed change

[needs SME confirmation] The "upgradable later" wording (items 1 and 4), the allowed set `5.0`/`6.0`/`7.0`/`8.0` and the `8.0` default (items 1-4), and the driver-support sentence in item 5 depend on Open questions 1-3. Remove these tags once they are confirmed.

### 1. `skills/azure-deployment/SKILL.md` (parameter table, line 157)

Replace the row with:

```
| MongoDB server version | `8.0` | Allowed: `5.0`, `6.0`, `7.0`, `8.0` (default `8.0`). Set per cluster at create time and upgradable later to a newer major version; it is not an account-wide level. This is **not** the RU-based Azure Cosmos DB for MongoDB; its 3.2–4.4 "compatibility levels" do not exist here. Read an existing cluster's value with `az resource show -g <rg> -n <cluster> --resource-type Microsoft.DocumentDB/mongoClusters --query properties.serverVersion` (or run `az documentdb mongocluster show -g <rg> -n <cluster>` with the documentdb extension and read `serverVersion` from the output). |
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

### 4. `skills/connection/SKILL.md` (new subsection after "### Authentication", after line 75)

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

### 5. `skills/driver/SKILL.md` (Rules list) and new `skills/driver/driver-check-server-version.md`

Add to the Rules list:

```markdown
- [driver-check-server-version](driver-check-server-version.md) — Pick the current stable driver release; do not pin a driver backwards to "match" a cluster's `serverVersion`. Read the cluster's version at startup when you need version-gated features.
```

New file, in the existing rule format (Category: Driver Best Practices, Priority: MEDIUM):

```markdown
# driver-check-server-version

**Category:** Driver Best Practices  **Priority:** MEDIUM

## Why it matters
Current official MongoDB drivers support server versions 5.0 through 8.0 [needs SME confirmation], so pinning an older driver line "for 7.0" gains nothing and loses fixes. A cluster's `serverVersion` is a property of that cluster, not a limit of Azure DocumentDB.

## Incorrect
    "mongodb": "^5.7.0"   // "because the cluster is MongoDB 7.0"

## Correct
Use the current stable driver, and log the server version at startup:
    const info = await client.db("admin").command({ buildInfo: 1 });
    console.log("serverVersion", info.version);
(PyMongo: `client.server_info()["version"]`.)

## References
- https://learn.microsoft.com/azure/documentdb/compatibility-query-language
- https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility
```

## Evidence

Run folders from the experiment (no connection details included):

- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json` — Q10 graded wrong: lists 3.2/3.6/4.0.
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` — Q10 graded wrong: "compatibility up to MongoDB 4.x/5.0".
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` — Q10 graded outdated: "depends on account serverVersion setting".
- `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json` (Q10) and `01-prompt-review.md:50-51` — single-version belief carried into the driver choice.
- `runs/04-customer-journey-mapper/20261124-203553/events.jsonl` — build decision: `mongodb ^5.7.0` "compatible with ... MongoDB 7.0 wire protocol".
- `runs/10-wealth-management-rag-portal/20261124-201449/events.jsonl` — build decision: `pymongo>=4.3,<5` "supports MongoDB 7.0 wire protocol".

## Open questions

1. [needs SME confirmation] Driver version floors: the source draft claimed current Node `mongodb` 6.x, PyMongo 4.x, Java 5.x, Go 2.x and .NET 3.x drivers all support 5.0–8.0 servers against Azure DocumentDB. The reviewer flagged driver floors (especially .NET and Java) as unverified, so the proposed rule names no driver versions, and its general sentence that current drivers support 5.0 through 8.0 stays tagged until confirmed.
2. [needs SME confirmation] That a cluster's major `serverVersion` can be upgraded in place after creation, and to which targets.
3. [needs SME confirmation] That `5.0`, `6.0`, `7.0` and `8.0` are all still accepted at create time in every region (no version retired or in preview), and that `8.0` is the right default.
4. [needs SME confirmation] The exact field path of `serverVersion` in `az documentdb mongocluster show` output (top level or under `properties`), so the CLI hint can give a precise `--query`.

Out of scope for this PR: the experiment harness describes its test cluster as "MongoDB 7.0 wire protocol"; relabelling it "this cluster's serverVersion" would stop the model generalising it. That harness (abinav2307/azure-documentdb-agent-readiness) belongs to a colleague, so that change should be coordinated with them.

## Source drafts

- 026-believes-the-supported-mongodb-server-versions-are-the-ru-er.md
