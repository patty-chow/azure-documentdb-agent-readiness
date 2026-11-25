---
title: "Learn: add a tool-agnostic connection-string reference, a \"check what your credentials can do\" section, and recommended production driver/bulk-write settings"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P2
sample_count: 4
findings: 4
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Learn docs: add a canonical connection-string reference, a credentials-permission check, and recommended production driver / bulk-write settings for Azure DocumentDB

## What happens today

The full Azure DocumentDB connection string, including the two options that differ from a stock MongoDB URI (`retrywrites=false` and `maxIdleTimeMS=120000`), is spread across pages that are each scoped to one tool or one auth method:

- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell shows the native-auth (SCRAM-SHA-256) string only inside `mongosh` command lines, with no explanation of the options.
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control has an option table under "Get cluster credentials" (`scheme`, `host`, `tls`, `authMechanism`, `retrywrites`, `maxIdleTimeMS`), but it lists `authMechanism` as `MONGODB-OIDC` (Entra ID only). It also says only that "the remaining recommended settings are best practice configuration settings", with no reason for `retrywrites=false` or `maxIdleTimeMS=120000`.
- The quickstarts repeat the string inside their own `.env` examples.

No page states the native-auth placeholder once as a reference, explains each option, covers both the `<cluster>.mongocluster.cosmos.azure.com` and `<cluster>.global.mongocluster.cosmos.azure.com` hosts, and is linked from every quickstart.

`db.runCommand({connectionStatus: 1})` appears on the mongosh page only as an "am I connected" check. The RBAC and secondary-users pages (https://learn.microsoft.com/en-us/azure/documentdb/secondary-users) document the built-in roles (`readWriteAnyDatabase` + `clusterAdmin`, assigned together, for read-write; `readAnyDatabase` for read-only) and preview custom roles. They show `usersInfo` only for listing users as an administrator. Neither page tells an application holding a URI how to find out what that URI is allowed to do, for example whether it can create collections and indexes.

The limitations page (https://learn.microsoft.com/en-us/azure/documentdb/limitations, "Batch limits") states the 25,000-writes-per-batch ceiling but gives no starting point for sizing unordered `bulkWrite` batches. No Learn page gives a recommended production driver option set (pool size, idle timeout, server-selection timeout, retryWrites). The DocumentDB Agent Kit's `skills/connection/SKILL.md` has per-workload pool tables, but Learn has nothing for the kit to cite.

## Why it matters

An experiment had gpt-5-mini build 100 Azure DocumentDB sample apps with the DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers. In it:

- 4 samples logged "could not find" gaps on exactly these four points:
  - a canonical placeholder to copy into a README (`16-atm-network-status-monitor`, `11-preference-center-consent-store`)
  - whether the supplied URI can create collections, indexes and roles (`15-supplier-po-management`)
  - a one-line production driver option set (`01-unified-customer-profile-store`)
  - a default unordered-bulkWrite batch size for an M30 (`02-real-time-event-stream-ingestion`)
- The string is never stated once as a reference, and the generated docs drifted. 48 generated README/.env.example files show an Azure DocumentDB host placeholder, and 40 of them omit `retrywrites=false`.
- 19 samples hard-coded `retryWrites: true` in application code, for example `02-real-time-event-stream-ingestion/app/src/db.js` and `03-core-banking-transaction-ledger/app/src/db.js`. This overrides the portal-issued URI. The Agent Kit contradicts itself: `skills/connection/SKILL.md` shows a placeholder ending in `retryWrites=true`, while `skills/azure-deployment/SKILL.md` says `retrywrites=false` is required. A Learn reference would give the kit a source of truth. The kit's contradiction should also be filed separately against Azure/documentdb-agent-kit.
- No generated app checked what its credentials could do (no `connectionStatus` or `usersInfo` call in any app code) before running `createCollection` or `createIndex`. One builder's plan was to "attempt a safe index-list call" as a guess.

## Proposed change

### 1. Connection string reference (new section or new how-to)

This can be a new page, `how-to-connection-string`, or a section at the top of `how-to-connect-mongo-shell`. Link it from every quickstart's "Get connection string" step, and make it the native-auth counterpart of the existing option table on the RBAC page. It should contain:

```
mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

Add a note that `<cluster-name>.global.mongocluster.cosmos.azure.com` is the global read-write endpoint for replica configurations, and that Entra ID uses `authMechanism=MONGODB-OIDC` (link to the RBAC page). Then add a table:

| Option | Value | Why |
|---|---|---|
| `tls` | `true` | TLS must be enabled (already stated on the RBAC page) |
| `authMechanism` | `SCRAM-SHA-256` | native DocumentDB user auth; `MONGODB-OIDC` for Entra ID |
| `retrywrites` | `false` | product team to state the engine behaviour and what a driver left at its default (`true`) will see |
| `maxIdleTimeMS` | `120000` | product team to state the idle-connection behaviour this value matches |

Add a one-line note: "Don't set `retryWrites: true` in driver options. Most drivers let client options override the URI." Also include the local DocumentDB (Docker) variant so READMEs can show both: `mongodb://<username>:<password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`, marked as local-only.

### 2. "Check what your credentials can do" (add to how-to-connect-role-based-access-control or secondary-users)

Add a short section showing, in `mongosh` and in one driver, how a connected user inspects its own roles:

```javascript
db.runCommand({ connectionStatus: 1, showPrivileges: true })
db.getSiblingDB("admin").runCommand({ usersInfo: "<username>" })
```

The product team should confirm which of these the service supports for a non-administrative user, and with which options. Next to the commands, add a table that maps the service's built-in roles to what they permit:

| Role | Can do |
|---|---|
| Built-in administrator | Full access, including user management |
| `readWriteAnyDatabase` + `clusterAdmin` (always assigned together) | Read and write data; create and drop collections and indexes. No user management. |
| `readAnyDatabase` | Read-only access |
| Custom roles (preview) | `find`, `insert`, `update` and `delete` only. Index, collection and database lifecycle actions are not available to custom roles. |

An agent handed a `DOCUMENTDB_URI` needs this to decide whether it can create the schema or must ask for different credentials.

### 3. "Production driver settings" and "Bulk write sizing" (new best-practices section, cross-linked from limitations)

- Give one recommended value set per workload shape, in both URI-option and driver-option form. For a long-running web service that could be, for example: `maxPoolSize` 50, `minPoolSize` 5, `maxIdleTimeMS` 120000, `serverSelectionTimeoutMS` 5000, `socketTimeoutMS` 30000, `retryWrites` false. Add a serverless column (small pool, short idle) and a batch-job column (larger pool). These numbers are illustrative, and the product team should set the real ones. The ask is that one documented set exists.
- Add a per-tier bulk-write table, next to the existing 25,000 ceiling, that gives a starting point for unordered `bulkWrite`. It should cover operations per batch, concurrent batches per client, and when to split work by `_id` range. Add a sentence on inspecting `writeErrors` instead of re-running whole batches. The values must come from the product team; the experiment has no measured numbers.

## Evidence (run folders from the experiment; no connection strings included)

- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json` (information_gaps: connection-string shape for the target cluster)
- `runs/15-supplier-po-management/20261124-184929/02-readiness.json` (information_gaps: permissions on the provided DOCUMENTDB_URI)
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json` (information_gaps: recommended driver retry and timeout values for production)
- `runs/02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` and `.../app/src/db.js` (bulkWrite batch-size gap; `retryWrites: true` hard-coded at line 24)
- `runs/03-core-banking-transaction-ledger/20261124-200452/app/src/db.js` (`retryWrites: true` hard-coded at line 23)
- `runs/11-preference-center-consent-store/20261124-204614/02-readiness.json` (information_gaps: canonical connection-string form)

## Verification

### 1. Already covered? partially_covered

- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell shows the full SCRAM-SHA-256 string inside `mongosh` commands with no per-option explanation. It uses `connectionStatus` only as an "am I connected" test, with no `showPrivileges`.
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ("Get cluster credentials") already has an option table: tls `true`, authMechanism `MONGODB-OIDC`, retrywrites `false`, maxIdleTimeMS `120000`. It says the tls setting "must also be enabled" and that the rest are "best practice configuration settings". That table is Entra-only and has no rationale, so item 1 is partly covered. The original draft wrongly said the string appears only on tool-specific pages; the body above now cites this table.
- https://learn.microsoft.com/en-us/azure/documentdb/secondary-users and the RBAC page document the built-in roles and `usersInfo` for listing users as an administrator. No page tells a URI holder how to check its own privileges, so item 2 is not covered.
- https://learn.microsoft.com/en-us/azure/documentdb/limitations ("Batch limits") gives only "Maximum writes per batch operation: 25,000 writes". There is no sizing guidance. The DocumentDB TOC has no driver, connection-pooling or bulk-write page; its only best-practices pages are indexing and HA/DR. Items 3a and 3b are not covered on Learn.
- Agent Kit: `skills/connection/SKILL.md` lines 98-135 already have per-workload `maxPoolSize` and `serverSelectionTimeoutMS` tables, so the driver-settings content exists in the kit but not on Learn. Line 60 of the same file shows `retryWrites=true`, which conflicts with `skills/azure-deployment/SKILL.md` line 291, a kit defect that belongs in a separate issue. The documentdb-mcp clone has nothing relevant.

### 2. Premise true? confirmed (with corrections applied)

The core premise holds: Learn has no single native-auth connection-string reference with rationale, no self-permission check, no production driver settings and no bulk-write sizing. Corrections applied to the body:
- The original draft said the RBAC page mentions `readWrite`, and it proposed a role table of `clusterAdmin`, `readWrite` and `read`. Per the secondary-users and RBAC pages, the supported built-in roles are `readWriteAnyDatabase` with `clusterAdmin` (which "must be granted together" for read-write), and `readAnyDatabase` for read-only. Custom roles (preview) support only `find`, `insert`, `update` and `delete`, with no index or collection lifecycle privileges. The table was rewritten to match.
- The original said the canonical string appears only inside tool-specific pages. The RBAC page has an option table, for OIDC. The text now says so.
- The original stats ("56 of 68" READMEs, "88 placeholders", "12 samples") did not reproduce. A recount over the run folders found 40 of 48 README/.env.example files with an Azure DocumentDB host placeholder omitting `retrywrites=false`, and 19 sample slugs with `retryWrites: true` in app code. The unverified "13 samples" claim was removed.
- The local-emulator string now includes `<username>:<password>`, matching the kit's `skills/local-deployment/local-env-driven-config.md` usage. Whether `showPrivileges` is supported on `connectionStatus` is left for the product team to confirm.
- The illustrative pool and bulk numbers are marked as placeholders for the product team, not stated as facts.

### 3. Maintainer skeptic: confirmed

The change names specific pages (how-to-connect-mongo-shell, how-to-connect-role-based-access-control or secondary-users, limitations) and concrete content (placeholder string, option table with rationale, self-check commands, role-capability table, driver-settings and bulk-sizing tables). It is specific to Azure DocumentDB: `retrywrites=false`, `maxIdleTimeMS=120000`, the paired `readWriteAnyDatabase`+`clusterAdmin` role, and the 25,000 ceiling. Items 1 and 2 are acceptable as written. Item 3 depends on the product team supplying the numbers, which the body now states. Learn docs is the right target. The kit's `retryWrites=true` contradiction should be a separate Azure/documentdb-agent-kit issue.

## Finding ids

- F0160
- F0269
- F2627
- F2659
