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
open_questions: 2
---

# Document the serverVersion choice in the azure-deployment, connection and driver skills

## What happens today

Nothing in the kit tells an agent which MongoDB server versions an Azure DocumentDB cluster can run, or how to read the version of the cluster it is connected to. Models trained on the older request-unit (RU) based Azure Cosmos DB for MongoDB fill the gap with that service's story, which does not apply here. Asked "Which MongoDB wire protocol or server versions are supported?" without grounding, gpt-5-mini answered in two wrong ways:

- **RU-era answer:** 3.2 / 3.6 / 4.0 / 4.2 / 4.4 as an account-wide "compatibility level", with 5.0 / 6.0 "in preview".
- **Single-version answer:** "the service exposes a MongoDB 7.0 wire protocol", generalised from the experiment's own description of its test cluster as "MongoDB 7.0 wire protocol" in `loop/run-environment.md`, a label that filing H11 shows disagrees with the cluster's control plane (server version 8.0).

Learn already documents the range (overview, at-a-glance, and the per-version columns of the query-language compatibility page), and grounded answers found it. The gap is in the kit, which loads in every session:

- `skills/azure-deployment/SKILL.md:157`: the "MongoDB server version" row shows `8.0` with an empty Notes cell and no allowed values.
- `skills/azure-deployment/references/bicep-cluster-template.md:54-55`: `param serverVersion string = '8.0'` has no `@allowed`, unlike `haTargetMode` directly above it.
- `skills/azure-deployment/references/terraform-cluster-template.md:91-93`: `variable "mongo_version"` has no `validation` block, unlike `high_availability_mode` directly above it.
- `skills/connection/SKILL.md` and `skills/driver/SKILL.md` never mention `serverVersion`, wire versions, `buildInfo` or `maxWireVersion`.

## Why it matters

In one experiment run (100 sample app prompts, gpt-5-mini with the kit and the DocumentDB, Azure and Learn MCP servers), the cold answer was wrong, outdated or partly wrong in 55 runs across **52 of the 100 samples**. Counts are from that single run, and may move on a re-run.

The belief then reached the code. In 16 of those runs the build stage logged a driver choice justified by "the cluster is MongoDB 7.0": `mongodb` npm pinned to `^5.7.0`, `pymongo>=4.3,<5`, or Mongoose 7.x picked "for the 7.0 wire protocol". The agent treats one cluster's version as a product limit, pins drivers backwards to match it, and avoids operators it thinks are "not in 4.x". The 3.x/4.x levels never existed on this service. Backwards pinning also produced hard failures: 13 runs hit `npm ERR! notarget` for driver versions that do not exist (for example `mongodb@^5.10.0`, `mongodb@^5.12.0`, `mongoose@^7.14.0`), such as `runs/03-core-banking-transaction-ledger/20261124-200452/events.jsonl`.

## Proposed change

The facts below follow `findings/phase4/DECISIONS.md` (SME topics 4 and 11): the documented version set is `5.0`, `6.0`, `7.0`, `8.0` (Learn FAQ; azurerm provider validation); the service default when `serverVersion` is omitted is "the latest available version" and every current Learn provisioning page sets `8.0`; the version is changed in place (Learn how-to-upgrade-cluster, `az documentdb mongocluster update --server-version`, azurerm in-place PATCH), and kit text says not to lower it because the control plane accepted a downgrade with no warning in the managed test of 2026-11-25 (M30, one shard, HA off; one downgrade, 8.0 to 7.0); and the CLI output key is `properties.serverVersion`. The two points still open (Microsoft-specific tested driver floors, and whether brand-new `5.0`/`6.0` clusters are still accepted) are listed under Open questions and do not change the proposed text.

### 1. `skills/azure-deployment/SKILL.md` (parameter table, line 157)

Replace the row with:

```
| MongoDB server version | `8.0` | Allowed: `5.0`, `6.0`, `7.0`, `8.0` (default `8.0`; when omitted the service uses the latest available version). Check the current list in the [Azure DocumentDB FAQ](https://learn.microsoft.com/azure/documentdb/faq). Set per cluster at create time and changed in place with `update --server-version`. Do not lower it: in one test (M30, one shard, HA off) a downgrade from 8.0 to 7.0 was accepted with no warning. On `update`, leaving `--server-version` out keeps the current version (the CLI help's "Defaults to the latest available version if not specified" is wrong there). It is not an account-wide level. This is **not** the RU-based Azure Cosmos DB for MongoDB; its 3.2–4.4 "compatibility levels" do not exist here. Read an existing cluster's value with `az documentdb mongocluster show -g <rg> -n <cluster> --query properties.serverVersion` (documentdb extension, Azure CLI 2.75.0 or later) or `az resource show -g <rg> -n <cluster> --resource-type Microsoft.DocumentDB/mongoClusters --query properties.serverVersion`; upgrade with `az documentdb mongocluster update -g <rg> -n <cluster> --server-version 8.0`; the command returns while the cluster still reads `Updating`, so poll `show` until `provisioningState` is `Succeeded` and `clusterStatus` is `Ready`. |
```

### 2. `skills/azure-deployment/references/bicep-cluster-template.md` (lines 54-55)

```bicep
@description('MongoDB wire-protocol server version. Allowed: 5.0, 6.0, 7.0, 8.0 (see the Azure DocumentDB FAQ for the current list). Omitting serverVersion makes the service pick the latest available version. Changed in place after creation; do not lower it (a downgrade was accepted without warning in one test).')
@allowed([
  '5.0'
  '6.0'
  '7.0'
  '8.0'
])
param serverVersion string = '8.0'
```

### 3. `skills/azure-deployment/references/terraform-cluster-template.md` (lines 91-93)

The azurerm provider already restricts `azurerm_mongo_cluster.version` to these four values (`validation.StringInSlice`), so the kit's variable should match it:

```hcl
variable "mongo_version" {
  type        = string
  description = "MongoDB wire-protocol server version. Allowed: 5.0, 6.0, 7.0, 8.0 (see the Azure DocumentDB FAQ for the current list). Changing it later updates the cluster in place; do not lower it (a downgrade was accepted without warning in one test)."
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

Each Azure DocumentDB cluster has its own `serverVersion`: `5.0`, `6.0`, `7.0` or `8.0`, set per cluster at create time and changed in place; raise it, never lower it (a downgrade was accepted without warning in one test). There is no account-wide "compatibility level", and the 3.x/4.x versions of the request-unit based Cosmos DB for MongoDB do not apply.

Before relying on a version-gated operator or stage, read the version from the cluster you are actually connecting to:

- `az documentdb mongocluster show -g <rg> -n <cluster> --query properties.serverVersion` (or `az resource show ... --query properties.serverVersion`), or
- at runtime: `db.version()` / `db.adminCommand({ buildInfo: 1 }).version`, or `client.server_info()["version"]` in PyMongo (`hello.maxWireVersion` returns an integer wire version, not the "7.0"-style string: 25 on an 8.0 cluster, 21 on 7.0).

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
Learn names no minimum driver version: any driver that speaks the MongoDB wire protocol connects (Azure DocumentDB FAQ). MongoDB's own driver compatibility tables, read as the wire-protocol floor, mark the current driver lines as fully compatible with server versions 5.0 through 8.0 (PyMongo 4.9+, Node.js `mongodb` 6.9+, Java sync 5.2+, .NET/C# 2.29+, Go 2.1+, Rust 3.1+; Mongoose needs ^8.7.0 or ^9 for 8.x), so pinning an older driver line "for 7.0" gains nothing and loses fixes. A cluster's `serverVersion` is a property of that cluster, not a limit of Azure DocumentDB. Nor does it promise every feature of that MongoDB release: an 8.0 cluster reports wire version 25, so a driver may send 8.0-only commands such as the client-level `bulkWrite` (PyMongo 4.20.1 did, and the call failed at run time with code 2; other drivers were not tried); check the compatibility page before using a version-gated feature.

## Incorrect
    "mongodb": "^5.7.0"   // "because the cluster is MongoDB 7.0"

## Correct
Use the current stable driver, and log the server version at startup:
    const info = await client.db("admin").command({ buildInfo: 1 });
    console.log("serverVersion", info.version);
(PyMongo: `client.server_info()["version"]`.)

## References
- https://learn.microsoft.com/azure/documentdb/compatibility-query-language
- https://learn.microsoft.com/azure/documentdb/faq
- https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility
- https://www.mongodb.com/docs/drivers/compatibility
```

## Evidence

Run folders from the experiment (no connection details included):

- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json` — Q10 graded wrong: lists 3.2/3.6/4.0.
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` — Q10 graded wrong: "compatibility up to MongoDB 4.x/5.0".
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` — Q10 graded outdated: "depends on account serverVersion setting".
- `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json` (Q10) and `01-prompt-review.md:50-51` — single-version belief carried into the driver choice.
- `runs/04-customer-journey-mapper/20261124-203553/events.jsonl` — build decision: `mongodb ^5.7.0` "compatible with ... MongoDB 7.0 wire protocol".
- `runs/10-wealth-management-rag-portal/20261124-201449/events.jsonl` — build decision: `pymongo>=4.3,<5` "supports MongoDB 7.0 wire protocol".

## Resolved

1. Driver support for 5.0–8.0 clusters: settled as a wire-protocol floor, not a Microsoft-tested matrix. Learn names no driver version and says any wire-protocol driver connects; MongoDB's driver compatibility tables mark PyMongo 4.9+, Node.js `mongodb` 6.9+, Java sync 5.2+, .NET/C# 2.29+, Go 2.1+ and Rust 3.1+ as fully compatible with 5.0 through 8.0, and Mongoose's table requires ^8.7.0 or ^9 for 8.x. Sources: https://learn.microsoft.com/en-us/azure/documentdb/faq (updated 2026-11-07, "Which MongoDB versions and features does Azure DocumentDB support?" and "Are MongoDB drivers and tools compatible with Azure DocumentDB?"); https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language; https://www.mongodb.com/docs/drivers/compatibility.md; https://mongoosejs.com/docs/compatibility.html (DECISIONS.md, SME topic 4, item 4.8).
2. In-place upgrade: a cluster's major `serverVersion` can be upgraded in place after creation through the portal Upgrade button, `az documentdb mongocluster update --server-version` (a PATCH) or a change to azurerm `version` (no ForceNew); Learn lists no target versions beyond "the latest MongoDB version". The managed test of 2026-11-25 upgraded an M30 cluster from 7.0 to 8.0 in 128 seconds while once-a-second probes (`hello`, an insert and a count) all succeeded; the wire version switched from 21 to 25 about 90 seconds in, and the `update` output still read `Updating`. Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-upgrade-cluster; https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster#az-documentdb-mongocluster-update; https://github.com/hashicorp/terraform-provider-azurerm/blob/main/internal/services/mongocluster/resources/mongo_cluster/r_update.go (lines 112-113) (DECISIONS.md, SME topic 11).
3. Allowed set and default: the documented set is `5.0`, `6.0`, `7.0`, `8.0`; `8.0` is the right default, and the service default when the property is omitted is "the latest available version". Sources: https://learn.microsoft.com/en-us/azure/documentdb/faq; https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/mongo_cluster and r_schema.go lines 246-254 (`StringInSlice` 5.0/6.0/7.0/8.0); https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/mongoclusters (`serverVersion`: "Defaults to the latest available version if not specified"); https://learn.microsoft.com/en-us/azure/documentdb/quickstart-cli, quickstart-bicep, quickstart-terraform and quickstart-portal (all set 8.0) (DECISIONS.md, SME topic 11).
4. Field path: `az documentdb mongocluster show` and `list` return the ARM resource body unflattened, so the key is `properties.serverVersion` (`--query properties.serverVersion`); observed on 2026-11-25 with the documentdb extension 1.0.0. Sources: https://github.com/Azure/azure-cli-extensions/blob/main/src/documentdb/azext_documentdb/aaz/latest/documentdb/mongocluster/_show.py (lines 172, 269-270); local observation 2026-11-25 (DECISIONS.md, SME topic 11).
5. Downgrade (former open question 2): not blocked in one test. `az documentdb mongocluster update --server-version 7.0` on an 8.0 cluster (M30, one shard, HA off) exited 0 after 94 seconds with no warning; `hello` then reported wire version 21 and `buildInfo` 7.0.0, with the same engine build, and raising it back to 8.0 worked. The Microsoft Q&A claim that version changes are upgrade-only is wrong for this cluster shape. The kit text therefore says "do not lower it" as advice, not as a control-plane rule. The `--server-version` help ("Defaults to the latest available version if not specified") is wrong on `update`, where leaving the flag out keeps the current version (from the documentdb extension 1.0.0 source, whose `update` reads the cluster and PATCHes the current body back; consistent with the managed test's Entra ID update without the flag, which left 8.0 in place, but not observed as such, because that cluster was already at the latest version). Sources: ENGINE-TESTS.md, Managed service; DECISIONS.md, SME topic 11, item 2.

## Open questions

1. [needs SME confirmation] Does Microsoft maintain Azure DocumentDB-specific tested driver floors per compatibility version (5.0–8.0), different from MongoDB's wire-protocol tables? No Learn page names a minimum or tested driver version, so the proposed rule recommends the current stable release and cites MongoDB's tables only as the floor (DECISIONS.md 4.8-open).
2. [needs SME confirmation] Does the control plane still accept `serverVersion` 5.0 and 6.0 for brand-new clusters, or only for existing ones? (Not tested by the managed test of 2026-11-25.) The FAQ lists all four and the azurerm provider validates them, but Learn gives no per-version lifecycle or retirement dates; the templates therefore list the four values, default to 8.0 and point to the FAQ for the current list (DECISIONS.md, SME topic 11, open item 3).

Out of scope for this PR: the experiment harness describes its test cluster as "MongoDB 7.0 wire protocol"; relabelling it "this cluster's serverVersion" would stop the model generalising it. That harness (abinav2307/azure-documentdb-agent-readiness) belongs to a colleague, so that change should be coordinated with them.

## Source drafts

- 026-believes-the-supported-mongodb-server-versions-are-the-ru-er.md
