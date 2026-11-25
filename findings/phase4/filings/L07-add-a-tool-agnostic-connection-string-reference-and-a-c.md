---
id: L07
title: "Add a tool-agnostic connection-string reference and a credential-capabilities section"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P2
sample_count: 4
member_drafts:
  - 047-connection-docs-lack-one-canonical-placeholder-connection-st.md
open_questions: 7
---

# Add a tool-agnostic connection-string reference and a credential-capabilities section

## What happens today

The Azure DocumentDB connection string, including the two options that differ from a stock MongoDB URI (`retrywrites=false` and `maxIdleTimeMS=120000`), is spread across pages that are each scoped to one tool or one auth method:

- [Connect with mongosh](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell) shows the native-auth (SCRAM-SHA-256) string only inside `mongosh` command lines, with no explanation of the options.
- [Connect with role-based access control](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control), under "Get cluster credentials", has an option table (`tls`, `authMechanism`, `retrywrites`, `maxIdleTimeMS`), but it is written for Entra ID (`MONGODB-OIDC`) and calls the non-TLS options "best practice configuration settings" without saying why.
- Each quickstart repeats the string inside its own `.env` example.

No page states the native-auth placeholder once, explains each option, and is linked from every quickstart.

For permissions, the RBAC and [secondary users](https://learn.microsoft.com/en-us/azure/documentdb/secondary-users) pages document the built-in roles and show `usersInfo` only as an administrator listing users. The mongosh page uses `connectionStatus` only as an "am I connected" check. No page tells an application holding a URI how to find out what that URI may do, for example whether it can create collections and indexes.

Related gaps: the [limitations](https://learn.microsoft.com/en-us/azure/documentdb/limitations) page gives the 25,000-writes-per-batch ceiling but no starting point for sizing unordered `bulkWrite` batches, and no Learn page gives a recommended production driver option set (pool size, idle timeout, server-selection timeout).

## Why it matters

We had an AI coding agent build 100 Azure DocumentDB sample apps with the DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers available. All counts below come from that one experiment run and should be read as indicative.

- **4 of the 100 samples** stopped to record a "could not find" gap on exactly these points: the connection-string shape for the cluster, whether the supplied URI could create collections and indexes, recommended production driver retry and timeout values, and a default unordered-`bulkWrite` batch size for an M30 cluster. A fifth sample logged a "canonical connection-string form" gap in a separate 10-sample control run.
- With no single reference to copy, the generated docs drifted: 48 generated README or `.env.example` files show an Azure DocumentDB host placeholder, and 40 of them omit `retrywrites=false`.
- 19 samples set `retryWrites: true` in application code, which overrides the portal-issued URI in most drivers.

(The 48, 40 and 19 were recounted over all 105 run folders of the 100 samples, including the five samples that were re-run after an empty first build.)
- No generated app checked what its credentials could do before calling `createCollection` or `createIndex`; one agent's plan was simply to "attempt a safe index-list call".

A reference page would also give tools such as the DocumentDB Agent Kit a source to cite; the kit's own inconsistency is filed separately.

## Proposed change

### 1. Connection-string reference

A new how-to (for example `how-to-connection-string`) or a section at the top of the mongosh page, linked from every quickstart's "Get connection string" step, as the native-auth counterpart of the RBAC page's table:

```
mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

| Option | Value | Why |
|---|---|---|
| `tls` | `true` | TLS is required |
| `authMechanism` | `SCRAM-SHA-256` | Native DocumentDB users; use `MONGODB-OIDC` for Microsoft Entra ID (link to the RBAC page) |
| `retrywrites` | `false` | Product team to state the reason and what a driver left at its default will see |
| `maxIdleTimeMS` | `120000` | Product team to state the idle-connection behavior this value matches |

Also add:

- A note on the `<cluster-name>.global.mongocluster.cosmos.azure.com` host for replica configurations, if confirmed.
- One line: "Don't override these options in driver code (for example `retryWrites: true`); most drivers let client options take precedence over the URI."
- The local DocumentDB (Docker) form, marked local-only: `mongodb://<username>:<password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`.

### 2. "Check what your credentials can do"

Add this to the RBAC or secondary-users page. Show, in `mongosh` and in one driver, how a connected user inspects its own roles, for example:

```javascript
db.runCommand({ connectionStatus: 1, showPrivileges: true })
db.getSiblingDB("admin").runCommand({ usersInfo: "<username>" })
```

Next to it, add a table mapping roles to capabilities:

| Role | Can do |
|---|---|
| Built-in administrator | Full access, including user management |
| `readWriteAnyDatabase` + `clusterAdmin` (granted together) | Read and write data; create and drop collections and indexes; no user management |
| `readAnyDatabase` | Read only |
| Custom roles (preview) [needs SME confirmation] | `find`, `insert`, `update`, `delete` only; no collection or index lifecycle actions |

### 3. Production driver settings and bulk-write sizing

Add this as a best-practices section, cross-linked from the limitations page:

- Give one recommended option set per workload shape (long-running service, serverless, batch job), in both URI and driver-option form, covering `maxPoolSize`, `minPoolSize`, `maxIdleTimeMS`, `serverSelectionTimeoutMS`, `socketTimeoutMS` and `retryWrites` (consistent with the connection-string reference above). Values to come from the product team; the experiment has no measured numbers.
- Beside the 25,000 ceiling, give a per-tier starting point for unordered `bulkWrite`: operations per batch, concurrent batches per client, and when to split by `_id` range. Add a sentence on handling `writeErrors` rather than re-running whole batches.

## Evidence

- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`: gap on the exact connection-string shape
- `runs/15-supplier-po-management/20261124-184929/02-readiness.json`: gap on permissions of the provided URI
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: gap on production driver retry and timeout values
- `runs/02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` and `app/src/db.js`: gap on bulk-write batch size, plus `retryWrites: true` in code
- `runs/03-core-banking-transaction-ledger/20261124-200452/app/src/db.js`: another `retryWrites: true` in code
- `runs/11-preference-center-consent-store/20261125-064954/02-readiness.json` (control run): gap on the canonical connection-string form

## Open questions

1. [needs SME confirmation] Why is `retrywrites=false` required, and what happens when a driver leaves retryable writes on? Our internal drafts disagree. Some say retryable writes are not supported and cause write errors. Another notes that Learn does not say they are unsupported and calls the setting a best practice. We would like the engineering answer before either explanation goes into the table.
2. [needs SME confirmation] What idle-connection behavior does `maxIdleTimeMS=120000` match?
3. [needs SME confirmation] Can a non-administrative user run `connectionStatus` with `showPrivileges: true`, and `usersInfo` on itself?
4. [needs SME confirmation] Is the role-capability table accurate, and are custom roles still in preview?
5. [needs SME confirmation] When should the `.global.mongocluster.cosmos.azure.com` host be used?
6. [needs SME confirmation] What are the recommended pool, idle and timeout values per workload shape?
7. [needs SME confirmation] What are the per-tier starting points for unordered `bulkWrite` batch size and concurrency?

## Source drafts

- 047-connection-docs-lack-one-canonical-placeholder-connection-st.md
