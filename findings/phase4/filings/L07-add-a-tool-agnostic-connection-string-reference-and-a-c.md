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
open_questions: 5
---

# Add a tool-agnostic connection-string reference and a credential-capabilities section

## What happens today

The Azure DocumentDB connection string, including the two options that differ from a stock MongoDB URI (`retrywrites=false` and `maxIdleTimeMS=120000`), is spread across pages that are each scoped to one tool or one auth method:

- [Connect with mongosh](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell) shows the native-auth (SCRAM-SHA-256) string only inside `mongosh` command lines, with no explanation of the options.
- [Connect with role-based access control](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control), under "Get cluster credentials", has an option table (`tls`, `authMechanism`, `retrywrites`, `maxIdleTimeMS`), but it is written for Entra ID (`MONGODB-OIDC`) and calls the non-TLS options "best practice configuration settings" without saying why.
- Each quickstart repeats the string inside its own `.env` example.

No page states the native-auth placeholder once, explains each option, and is linked from every quickstart. The host form is also inconsistent across the first-contact pages: the six driver quickstarts (Node.js, Python, Java, C#, Go, Rust) hard-code `<your-cluster-name>.global.mongocluster.cosmos.azure.com` while the mongosh, Cloud Shell and portal quickstart pages, the training unit and the REST samples show the plain `<cluster-name>.mongocluster.cosmos.azure.com` host, and none of these connect pages (the six driver quickstarts, the portal quickstart, mongosh, Cloud Shell) says that the portal offers two strings (Self and Global read-write) or what the difference is. The difference is explained only on pages a native-auth user reads later (the RBAC page, the replica how-to, the replication concept pages, the Private Link page, the Mongoose tutorial) and in a note in the training unit.

For permissions, the RBAC and [secondary users](https://learn.microsoft.com/en-us/azure/documentdb/secondary-users) pages document the built-in roles and show `usersInfo` only as an administrator listing users. The mongosh page uses `connectionStatus` only as an "am I connected" check, and the only other Learn mention of `connectionStatus` is a release-notes entry (August 29, 2025) that uses a different role vocabulary from the RBAC pages. No page tells an application holding a URI how to find out what that URI may do, for example whether it can create collections and indexes.

Related gaps: the [limitations](https://learn.microsoft.com/en-us/azure/documentdb/limitations) page gives the 25,000-writes-per-batch ceiling but no starting point for sizing unordered `bulkWrite` batches, and no Learn page gives a recommended production driver option set (pool size, idle timeout, server-selection timeout).

## Why it matters

We had an AI coding agent build 100 Azure DocumentDB sample apps with the DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers available. All counts below come from that one experiment run and should be read as indicative.

- **4 of the 100 samples** stopped to record a "could not find" gap on exactly these points: the connection-string shape for the cluster, whether the supplied URI could create collections and indexes, recommended production driver retry and timeout values, and a default unordered-`bulkWrite` batch size for an M30 cluster. A fifth sample logged a "canonical connection-string form" gap in a separate 10-sample control run.
- With no single reference to copy, the generated docs drifted: 48 generated README or `.env.example` files show an Azure DocumentDB host placeholder, and 40 of them omit `retrywrites=false`.
- 19 samples set `retryWrites: true` in application code, which overrides the portal-issued URI in most drivers. Because the server does not de-duplicate a retried write, each of these apps can apply a non-idempotent write twice on a transient failure.

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
| `retrywrites` | `false` | Required. Azure DocumentDB does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice (documentdb/documentdb#767). Handle transient write failures in application code with idempotent operations (upserts, deterministic keys) |
| `maxIdleTimeMS` | `120000` | Product team to state the idle-connection behavior this value matches |

Also add:

- The two host forms, with the wording settled from Learn (RBAC page "Get cluster credentials", updated 2026-11-23; [how-to-cluster-replica](https://learn.microsoft.com/en-us/azure/documentdb/how-to-cluster-replica#use-connection-strings); [how-to-private-link](https://learn.microsoft.com/en-us/azure/documentdb/how-to-private-link); [tutorial-nodejs-mongoose](https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose), updated 2026-11-24): the portal offers a Self string (`<cluster-name>.mongocluster.cosmos.azure.com`, labelled "Self (always this cluster)") and, on the primary cluster only, a Global read-write string (`<cluster-name>.global.mongocluster.cosmos.azure.com`). Suggested text: "Copy the connection string from the portal (Cluster > Settings > Connection strings) or `az documentdb mongocluster list-connection-strings`. On a single cluster the Self string and the Global read-write string are interchangeable. If the cluster has or may get a cross-region replica, use the Global read-write string for writes so that a promotion needs no code change; the Self string of the old primary becomes read-only after promotion. Replica clusters expose only a Self string. Never construct the host from the cluster name; use the string the portal, CLI or REST API returns." In-region HA failover changes neither string.
- Link the reference from every first-contact connect page and make them agree: the six driver quickstarts tell the reader to copy "the Connection string field" (singular) but hard-code the `.global.` host, while the mongosh, Cloud Shell and portal quickstart pages show only the plain host; none names the Self and Global read-write fields. Add the one-sentence explanation above to each, or switch the quickstarts to the plain host.
- Explain why `retrywrites=false` is required, with the de-duplication reason. No Learn page (limitations, compatibility, connect) says this today; the RBAC page calls it a "best practice" without a reason. Suggested text: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Add the same statement to the limitations page.
- One line: "Don't override these options in driver code (for example `retryWrites: true`); most drivers let client options take precedence over the URI, and with `retryWrites: true` a retried non-idempotent write can be applied twice."
- The local DocumentDB (Docker) form, marked local-only: `mongodb://<username>:<password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`. This is the form on the [development-loop tutorial](https://learn.microsoft.com/en-us/azure/documentdb/development-loop); `authMechanism=SCRAM-SHA-256` is optional because the local gateway advertises only that mechanism.

### 2. "Check what your credentials can do"

Add this to the RBAC or secondary-users page. Show, in `mongosh` and in one driver, how a connected user inspects its own roles. Lead with `connectionStatus` and `showPrivileges: true`: the engine performs no privilege check on it and returns the caller's roles and privileges (`pg_documentdb/src/commands/users.c`, `connection_status`), the gateway enables it by default (`enableConnectionStatus`), and Azure's [release notes](https://learn.microsoft.com/en-us/azure/documentdb/release-notes) (August 29, 2025) document it returning roles and privilege sets. `usersInfo` on the caller's own name returns roles for secondary users (ListUser = yes in the RBAC page's permissions table); whether it also returns privileges for a non-administrative caller is not confirmed (open question below), so show it as the secondary check.

```javascript
db.runCommand({ connectionStatus: 1, showPrivileges: true })
db.getSiblingDB("admin").runCommand({ usersInfo: "<username>" })
```

Next to it, add a table mapping roles to capabilities. The role facts come from the [RBAC page](https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control) (updated 2026-11-23) and the engine (`users.c`, `ValidateAndObtainUserRole`): `readWriteAnyDatabase` and `clusterAdmin` must be granted together, `clusterAdmin` in that pair grants no user-management privileges, `readAnyDatabase` is the only standalone built-in role, and any other combination is rejected with "Roles specified are invalid. Only readAnyDatabase or readWriteAnyDatabase+clusterAdmin are allowed built-in roles."

| Role | Can do |
|---|---|
| Built-in administrator (`root`) | Full access, including user management |
| `readWriteAnyDatabase` + `clusterAdmin` (granted together) | Read and write data; create and drop collections and indexes; no user management |
| `readAnyDatabase` | Read only |
| Custom roles (preview) | `find`, `insert`, `update`, `delete` only; no collection or index lifecycle actions. Preview per [how-to-configure-role-based-access-control](https://learn.microsoft.com/en-us/azure/documentdb/how-to-configure-role-based-access-control) (Important box) and the [secondary users](https://learn.microsoft.com/en-us/azure/documentdb/secondary-users) "Preview limitations" section (no `updateRole`, no custom-to-custom inheritance) |

Also fix on the same pages:

- Document `connectionStatus` itself. Today Learn describes it only in the release notes (the mongosh page runs it only as a connectivity check), and that entry names roles ReadWrite, UserAdmin, Root and privilege sets dbAdmin, userAdmin, clusterMonitor, clusterManager, hostManager, while the RBAC and secondary-users pages use `readWriteAnyDatabase`, `clusterAdmin`, `readAnyDatabase` and `root`. Map the two vocabularies so an application can interpret the command's output.
- Reconcile the secondary-users page (updated 2026-11-17), whose "Choose an access scope" table lists `readWriteAnyDatabase` and `clusterAdmin` as separately assignable and adds a validate/repair step for users holding `readWriteAnyDatabase`, with the RBAC page (updated 2026-11-23), which says the two "must be granted together". The engine ships the standalone behaviour behind a flag whose compiled default is off; which state Azure runs is an open question below. Until it is answered the table above follows the RBAC page, which is accepted in either state.
- The [limitations](https://learn.microsoft.com/en-us/azure/documentdb/limitations) page's "Native DocumentDB secondary users" section still says database- or collection-scoped roles and `rolesInfo` are unsupported; the same-day secondary-users and how-to-configure-role-based-access-control pages document both as preview. Align it.

### 3. Production driver settings and bulk-write sizing

Add this as a best-practices section, cross-linked from the limitations page:

- Give one recommended option set per workload shape (long-running service, serverless, batch job), in both URI and driver-option form, covering `maxPoolSize`, `minPoolSize`, `maxIdleTimeMS`, `serverSelectionTimeoutMS` and `socketTimeoutMS`, with `retryWrites` set to `false` in every variant (consistent with the connection-string reference above). Values to come from the product team; the experiment has no measured numbers, and no Learn page publishes a per-tier connection limit ([compute-storage](https://learn.microsoft.com/en-us/azure/documentdb/compute-storage) names "Concurrency" as a sizing input with no cap), so pool sizes cannot yet be derived from a documented ceiling.
- State the retry model next to the option set, from sources that already exist: Azure DocumentDB has no request-unit throttling and never returns code 16500 or 429 (those are codes of the RU-based Azure Cosmos DB for MongoDB; the [troubleshooting](https://learn.microsoft.com/en-us/azure/documentdb/troubleshoot-common-issues) error table and the open-source engine's error mappings contain no throttling code), and the server sends no `RetryableWriteError` label, so drivers do not retry writes. The [reliability page](https://learn.microsoft.com/en-us/azure/reliability/reliability-documentdb) puts retry on the application: "Configure retries with exponential backoff, and limit the number of retry attempts ... design write operations to be idempotent so that retrying them is safe." Tell readers to treat connection errors and code 50 `ExceededTimeLimit` as transient, to retry idempotent writes in application code, and not to code against 16500/429.
- Beside the 25,000 ceiling, give a starting point for unordered `bulkWrite`: operations per batch, concurrent batches per client, and when to split by `_id` range. Learn today gives only the hard cap ("Maximum writes per batch operation: 25,000 writes. Batch operations exceeding 25,000 writes will fail." on the limitations and [max-document-size](https://learn.microsoft.com/en-us/azure/documentdb/max-document-size) pages) and, on [migration-options](https://learn.microsoft.com/en-us/azure/documentdb/migration-options), a method rather than a figure (run a trial migration on a representative sample and extrapolate; scale up during migration); the 1,000-documents-per-`insertMany` figure lives on the RU-based Cosmos DB for MongoDB page, a different service. Until the product team supplies per-tier numbers, present 1,000 operations per call with `ordered: false`, a handful of parallel workers and chunking well under 25,000 as a starting point, not a Learn figure. Note that collection-level `db.collection.bulkWrite()` works (it maps to `insert`/`update`/`delete`; the compatibility page's "bulkWrite: No" row is the MongoDB 8.0 database-level command), and ask the limitations page to name the error returned above 25,000 writes and whether `hello.maxWriteBatchSize` reflects 25,000. Add a sentence on handling `writeErrors` rather than re-running whole batches.

## Evidence

- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`: gap on the exact connection-string shape
- `runs/15-supplier-po-management/20261124-184929/02-readiness.json`: gap on permissions of the provided URI
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: gap on production driver retry and timeout values
- `runs/02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` and `app/src/db.js`: gap on bulk-write batch size, plus `retryWrites: true` in code
- `runs/03-core-banking-transaction-ledger/20261124-200452/app/src/db.js`: another `retryWrites: true` in code
- `runs/11-preference-center-consent-store/20261125-064954/02-readiness.json` (control run): gap on the canonical connection-string form

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- When to use the `.global.` host: never required. On a single cluster the Self (`<cluster>.mongocluster.cosmos.azure.com`) and Global read-write (`<cluster>.global.mongocluster.cosmos.azure.com`) strings are interchangeable; use the Global read-write string for writes on a cluster that has or may get a cross-region replica, because it follows the primary across a promotion while the old primary's Self string becomes read-only; replica clusters expose only a Self string; in-region HA failover changes neither. Sources: DECISIONS.md "Host forms" (SME topic 3); https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ("Get cluster credentials"); https://learn.microsoft.com/en-us/azure/documentdb/how-to-cluster-replica#use-connection-strings; https://learn.microsoft.com/en-us/azure/documentdb/how-to-private-link; https://learn.microsoft.com/en-us/azure/documentdb/availability-disaster-recovery-under-hood; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose.
- `connectionStatus` with `showPrivileges: true` as a non-administrative user: yes. The engine performs no privilege check on `connectionStatus` and returns the caller's roles and privileges, the gateway setting `enableConnectionStatus` defaults to true, and Azure's release notes (August 29, 2025) document the command on the service. Sources: DECISIONS.md "Microsoft Entra ID specifics" (SME topic 5); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/users.c (connection_status); https://github.com/documentdb/documentdb/blob/main/pg_documentdb_gw/documentdb_gateway_core/src/configuration/dynamic.rs (enableConnectionStatus); https://learn.microsoft.com/en-us/azure/documentdb/release-notes. (`usersInfo` on self returns roles; whether it returns privileges to a non-admin caller stays open below.)
- Custom roles still in preview: yes, with only `find`, `insert`, `update` and `delete` actions, no `updateRole` and no custom-to-custom inheritance. Sources: DECISIONS.md (SME topic 5); https://learn.microsoft.com/en-us/azure/documentdb/how-to-configure-role-based-access-control (Important box, updated 2026-11-17); https://learn.microsoft.com/en-us/azure/documentdb/secondary-users ("Preview limitations").
- Role-capability table: `readWriteAnyDatabase` and `clusterAdmin` must be granted together and the pair grants no user management, `readAnyDatabase` is the only standalone built-in role, and the engine rejects any other built-in combination; the table follows the RBAC page, which is valid whichever way the open flag question below is answered. Sources: DECISIONS.md (SME topic 5); https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (updated 2026-11-23); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/users.c (ValidateAndObtainUserRole).

## Open questions

1. [needs SME confirmation] What idle-connection behavior does `maxIdleTimeMS=120000` match? No Learn page or engine source consulted in DECISIONS.md explains the value.
2. [needs SME confirmation] On Azure, does `usersInfo` with `showPrivileges: true` on the caller's own name return privileges when the caller is a non-administrative (read-write or read-only) user? The engine default for `EnableUsersInfoPrivileges` is true and the release notes document privilege sets, but neither source states the non-admin-caller case.
3. [needs SME confirmation] Does the Azure service run with the engine's standalone `readWriteAnyDatabase` flag (`documentdb.enable_readwrite_any_database_role_enforcement`) on, making the RBAC page's "must be granted together" statement obsolete, or off, making the secondary-users page's standalone role table wrong?
4. [needs SME confirmation] What are the recommended pool, idle and timeout values per workload shape, and is there a per-tier connection limit (with code 261 `TooManyLogicalSessions` as what a client sees when it is reached)?
5. [needs SME confirmation] What starting batch size per M-series tier should be recommended for unordered `bulkWrite` loads, and does the Azure gateway advertise `hello.maxWriteBatchSize` as 25,000 (matching the engine cap) or the gateway's compiled default of 100,000?

## Source drafts

- 047-connection-docs-lack-one-canonical-placeholder-connection-st.md
