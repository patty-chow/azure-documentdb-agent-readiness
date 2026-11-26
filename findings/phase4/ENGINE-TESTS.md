# Engine tests: documentdb-local and the managed service

Open questions that depend on engine behaviour were tested on this Mac against the open-source
engine, image `ghcr.io/documentdb/documentdb/documentdb-local`, as pulled locally on 2026-09-25:
OCI version 0.117.0, revision 28cc0120, PostgreSQL 17.11, pgvector 0.8.6, wire version 21 (the
gateway advertises MongoDB 7.0.0). Note that the `latest` tag has since moved to engine 1.2.0;
these results are for 0.117; the rerun on 1.2.0 (see "Rerun" below) reproduced them apart from
`serverStatus`, and its new findings correct some of the readings.
The sections before "Managed service" are evidence about the open-source engine and gateway, not
proof of managed-service behaviour. Scripts and JSON reports with every raw response are in
`findings/phase4/engine-tests/`. The last section, "Managed service (2026-11-25)", repeats the tests
on a real Azure DocumentDB cluster; where it differs from the open-source results, it wins.

Each test was run by one agent and then rerun by a second agent against a fresh database. Seven of
the ten reruns were blocked because the Docker VM disk filled up two minutes after the last tester
finished (the 200,000-document query test plus the 25,001-document batch test exhausted the 25 GB
VM); those reruns verified the testers' raw replies against the scripts instead. `bulkwrite-forms`
and `registry-facts` reproduced exactly. `write-read-concerns` never ran and is marked inconclusive.

## Vector indexes (settles the "not an SME item" questions of topic 6)

- One vector index per path is enforced: a second `cosmosSearch` index on the same path fails with
  code 85 `IndexOptionsConflict` whether the options are identical ("Index already exists with a
  different name") or a different kind or `m` ("An equivalent index already exists with a different
  name and options").
- An identical `createIndexes` is a no-op: `ok: 1` with `note: "all indexes already exist"`.
- Same name, different options: code 86 `IndexKeySpecsConflict`.
- `listIndexes` reports the options under `cosmosSearchOptions`; there is no `cosmosSearch` key in
  the output on this gateway. Learn's vector-search page shows `cosmosSearch:` in its `getIndexes`
  sample. Either the managed gateway differs or the Learn sample is wrong: check on the managed
  service before the kit's ensure-index helper relies on one key. Checked since: the managed service
  also reports `cosmosSearchOptions` only, so the Learn sample is wrong (see "Managed service").
- HNSW builds on an empty collection; inserts and a correct search followed with no visible delay.
- IVF `numLists: 0` is rejected (code 67) with a message whose numbers are swapped: "numLists must be
  greater than or equal to 0, but was 1". Worth an engine issue. `numLists` far above the document
  count is accepted and the search still returns correct neighbours.
- Dimension caps are enforced identically for HNSW and IVF: 2001 uncompressed fails ("field cannot
  have more than 2000 dimensions for vector index"), 2000 works; with `compression: "half"` 4001
  fails ("more than 4000"), 4000 works, 2001 works. Matches the team's own test.
- BSON Binary vectors (subtypes 0 and 9) insert without error, are returned intact by `find`, and
  are absent from `$search` results over the same collection.

## Schema validation and partial unique indexes (topic 10)

- Validators are on in this build. A violating insert fails with write error code 121
  "Document failed validation", with no `codeName` and no `errInfo` details.
- `enum` and `oneOf` are accepted by `create` and `collMod` and enforced on insert. Learn's
  `$jsonSchema` page (updated 2026-01-28) still lists them as unsupported. The research found them
  added to the engine in July 2026, so the Learn page is stale for engine 0.117 and later; whether
  the managed service runs that build is the remaining question. Checked since: the managed cluster
  tested on 2026-11-25 enforces both; clusters on older builds may still reject them with code 9 or
  gate validators altogether (see "Managed service").
- `additionalProperties`, `allOf`, `anyOf`, `not`, `patternProperties`, `dependencies`,
  `minProperties` and `maxProperties` are rejected at `create` and `collMod`.
- `{ unique: true, partialFilterExpression: { key: { $exists: true } } }` is accepted and enforced:
  duplicate keys fail with 11000, documents without the key coexist. `{ key: { $gt: 0 } }` behaves
  the same for values inside the filter. `$exists: false` in a partial filter is rejected (code 67),
  and mixing `sparse` with `partialFilterExpression` is rejected (code 197).

## Transactions (topic 9)

- Write conflict between two transactions: the second update fails immediately with code 112
  `WriteConflict` and no `errorLabels` at all. Drivers' `withTransaction` retry loops key on the
  `TransientTransactionError` label, so they will not retry here. This is the behaviour engine issue
  documentdb/documentdb#339 describes; application code must retry on code 112 itself.
- `readConcern: { level: "snapshot" }` in a transaction: code 115 `CommandNotSupported`
  ("'Snapshot' read concern is not supported") on this image. `majority` and `local` are accepted.
- `commitTransaction` is idempotent (second call returns `ok: 1`). `abortTransaction` after commit:
  code 256 `TransactionCommitted`.
- A transaction idle for more than 30 seconds: the next write and the commit return code 1
  `InternalError` with a generic message and no labels; a later `abortTransaction` returns 251
  `NoSuchTransaction`. The gateway log shows PostgreSQL's `idle_in_transaction_session_timeout`
  killing the backend. The DECISIONS best guess of "251 on the next operation" was wrong for the
  first operation on this image; on 1.2.0 and on the managed service the next statement got code 1
  or 251 (on the service, 251 in 5 of 8 trials after a 36-second idle gap and at 45, 60 and 75
  seconds; see "Rerun" and "Managed service").

## Bulk writes (topic 9)

- Collection-level `bulkWrite` works, ordered and unordered, with per-op `writeErrors` on a duplicate
  `_id`. It is sent as separate insert, update and delete commands grouped by type, as every driver
  does.
- Client-level `MongoClient.bulkWrite` (the MongoDB 8.0 server command): PyMongo refuses it
  client-side because the wire version is 21, and the raw `bulkWrite` admin command returns code 59
  `CommandNotFound`.
- `hello.maxWriteBatchSize` is 25,000, so drivers split larger batches automatically;
  `insert_many` of 25,001 documents succeeded as 25,000 plus 1. A raw single command with 25,001
  operations fails with code 16 `InvalidLength`: "Write batch size must fall within the range of 1 to
  25000, but N operations were provided." That is the error the Learn limitations page could name.

## Query behaviour (topic 10)

- The two-stage `$setWindowFields` example (cumulative `documents: ["unbounded", "current"]` with
  `$sum` and `$max`, then `$group` with `$last`) runs and matches a client-side computation.
- `sortBy` is required for a bounded documents window (code 5339901) and for a range window
  (code 5339902); a fully unbounded window is accepted without it.
- `allowDiskUse` true and false are both accepted on `aggregate` and `find`, with identical results and
  timing on a 200,000-document in-memory sort; a non-boolean value fails with code 14 `TypeMismatch`.
  No behavioural difference was observable.
- Explain layout: `find` puts `queryPlanner.winningPlan` at the top level; `aggregate` returns a
  `stages[]` array whose first element is `$cursor.queryPlanner.winningPlan`; a `$search` cosmosSearch
  pipeline shows `FETCH` over `IXSCAN` on the vector index with `cosmosSearchCustomParams`.
- An unindexed predicate over 200,000 documents did not produce `COLLSCAN`: the plan was `FETCH` with
  a runtime filter over a bitmap `IXSCAN` on `_id_`, with all 200,000 documents examined. A rule that
  looks for `COLLSCAN` in explain output will miss full scans on this engine; checking
  `totalDocsExamined` against `nReturned` is the reliable signal. Corrected since: top-level
  `executionStats` describe only the root stage, so a `LIMIT` or `SORT` root can hide a scan;
  compare the two on the `FETCH` or `COLLSCAN` stage that reports both (see "Rerun" and "Managed
  service").
- `maxTimeMS: 1` on aggregate fails with code 50, but `codeName` is `ExceededTimeLimit`
  ("Query exceeded command timeout of 1ms"), not MongoDB's `MaxTimeMSExpired`; the string
  `MaxTimeMSExpired` does not exist in the gateway binary. Whether `find` enforces it was inconclusive.

## TTL (topic 10)

- A compound TTL index is rejected (code 67: "TTL indexes work only on single fields"); a second
  single-field TTL index on another field is accepted.
- The purge is a `pg_cron` job (`documentdb_api_internal.delete_expired_rows()`) that runs once a
  minute on the minute. Only BSON Date values expire; string, number and missing values survived
  every run in a four-minute window. Observed lag after eligibility: 0 to about 60 seconds.

## Local gateway parity (topic 12)

Not available on image 0.117: `createSearchIndexes` (code 115), `$search` with `text` (code 40324
"Unrecognized $search option: text"), `$listSearchIndexes` (code 115 "stage is not enabled"),
change streams (code 115 "Stage $changeStream is not supported yet in native pipeline"),
`vector-diskann` (code 67 "Invalid search index kind"; only `hnsw` and `ivfflat` access methods
exist), `$rankFusion` (code 40324), `serverStatus` (code 115). Available: `currentOp` (command and
stage), `connectionStatus` with `showPrivileges`, HNSW and IVF vector indexes, transactions,
`$jsonSchema`. So the local container can test the data model, indexes, transactions and vector
search with HNSW or IVF, and cannot test full-text search, change streams, DiskANN or Entra ID
(`saslSupportedMechs` is SCRAM-SHA-256 only).

## Driver floors (topic 4)

- `AsyncMongoClient` is absent in PyMongo 4.8.0 and present from 4.9; 4.9, 4.11 and 4.13 all import
  and ping the engine asynchronously.
- `pip install "beanie>=2,<3"` resolves Beanie 2.2.0 with PyMongo 4.20 and no Motor; its metadata
  requires `pymongo>=4.11.0,!=4.15.0,<5`. A full init, insert, find and delete round trip on
  `AsyncMongoClient` works against the engine.
- MONGODB-OIDC first appears in the PyMongo 4.7.0 changelog (Apr 2024) and in the Node driver 6.7.0
  release notes (May 29 2024); 6.6.0's notes do not mention it.

## Registry facts (topics 12 and 13)

- `documentdb-mcp-server` on npm is not Microsoft's package. Version 0.1.0 was published on
  2026-11-24 by an unaffiliated maintainer, with no repository, homepage or README, two files, and a
  binary named `documentdb-mcp-local`. The kit's `mcp.json` runs `npx -y documentdb-mcp-server`, which
  would execute this package. `@azure/documentdb-mcp-server` and `@microsoft/documentdb-mcp-server`
  are both unpublished. This needs attention before anything else in the kit: see the MCP setup filing.
- `langchain-azure-cosmosdb` latest is 1.0.1 (2026-09-24), Python 3.11 or newer, langchain-core 1.x;
  it does not list `pymongo` among its dependencies, so the kit must install it explicitly.
- `llama-index-vector-stores-azurecosmosmongo` latest is 0.9.0 (2026-08-31), llama-index-core 0.13
  to 0.14.
- A LlamaIndex TypeScript store exists under another name: `@llamaindex/azure` 0.2.1 exports
  `AzureCosmosDBMongoDBVectorStore` (mongodb driver 6.21).
- GHCR tags for `documentdb-local`: `latest` = `1.2` = `pg17-1.2.0`; `stable` = `1.0` = `pg17-1.0.0` =
  `pg17-1.0.1`; versioned tags `pgNN-X.Y.Z` exist for pg15, pg16, pg17 from 0.109.0 and pg18 from
  0.114.0. CI should pin `pg17-1.2.0` (or the digest) rather than `latest`.

## Incidental observation (topic 2)

When its PostgreSQL backend is down, the gateway keeps accepting TLS connections and answers every
request, including `hello` and `saslStart`, with code 1 `InternalError` and a generic message and no
labels. A client cannot distinguish "backend down" from any other internal error.

## Rerun on engine 1.2.0 (2026-11-25)

All nine tests were rerun on a fresh `documentdb-local:pg17-1.2.0` container (engine release 1.2-0,
commit 965b6e7a, built 2026-11-12, PostgreSQL 17.12, pgvector 0.8.7, wire version 21), each followed
by an independent reproduction against a fresh database; every reproduction ran. Scripts and raw
reports are in `findings/phase4/engine-tests-1.2/`. Note that the managed service reports a newer
engine (`hello.internal.documentdb_versions` 2.2-1 and 2.3.0, wire version 25), so these are still
open-source results.

**What changed from 0.117.** Only `serverStatus`: it now returns `ok: 1` in MongoDB's layout
(`process: "mongod"`, `storageEngine: "documentdb"`), but its counters are fixed placeholders that do
not move under load (opcounters, network bytes and connections never change), so it is not usable for
metrics. Every other result above reproduced on 1.2.0 with the same code, codeName and message,
including: one vector index per path (85), same-name conflict (86), `listIndexes` reporting
`cosmosSearchOptions` with no `cosmosSearch` key, the swapped numbers in the IVF `numLists` error, the
2,000 and 4,000 dimension caps, Binary vectors absent from results, `enum` and `oneOf` enforced and the
other keywords rejected, code 112 with no labels on a write conflict, snapshot read concern rejected in
a transaction (115), client-level `bulkWrite` unavailable, the 25,000 batch cap (16), the TTL rules,
and the parity gaps (no full-text search, change streams, DiskANN, `$rankFusion` or MONGODB-OIDC).

**New findings on 1.2.0.**

- **Transactions do not isolate reads from concurrent commits.** Transaction B read a value, A
  incremented it and committed, B's second read in the same transaction returned A's value, and B's
  write based on its first read committed without error, losing A's update. This reproduced in 5 of 5
  runs. Treat multi-document transactions as read-committed: guard read-modify-write with a
  conditional update on the value read, not with a transaction alone.
- **30 seconds is a lifetime limit, not only an idle limit.** Transactions that wrote every 2 to 8
  seconds were still ended with 251 `NoSuchTransaction` ("Cannot continue transaction N") between 32
  and 44 seconds; one in nine committed. An idle transaction's next write returns code 1
  `InternalError` or 251, depending on a race between PostgreSQL's idle timeout and the gateway's sweep.
- **No error labels anywhere.** None of 213 captured error replies carried `errorLabels`, and the
  gateway binary contains no `TransientTransactionError`, `UnknownTransactionCommitResult` or
  `RetryableWriteError` string. PyMongo's `with_transaction` ran its callback once and re-raised the
  112 in 5 of 5 runs; it retried only when the label was added client-side. The 112 arrives after the
  gateway's short lock timeout (about 20 to 30 ms), not after the other transaction commits.
- **`COLLSCAN` does appear, once statistics exist.** Right after a 100,000-document load, unindexed
  finds planned as `FETCH` over a bitmap `IXSCAN` on `_id_`; after PostgreSQL analyzed the table, the
  same finds planned as `COLLSCAN`. The earlier "no `COLLSCAN`" result was a fresh-statistics artefact.
  Top-level `executionStats` describe only the root stage (a `SORT` or `LIMIT` on top hides the
  documents examined below it), and parallel plans report per-loop averages, so neither `COLLSCAN` nor
  top-level `totalDocsExamined` alone is a reliable full-scan check.
- **`maxTimeMS` is per command.** It is not cumulative across `getMore`; a `getMore` that carries its
  own `maxTimeMS` is limited on its own and, on expiry, the cursor is gone (43 `CursorNotFound`).
  Expiry is code 50 with codeName `ExceededTimeLimit`.
- **Write concerns are all accepted silently.** `w:0`, `w:1`, `"majority"`, `w:2`, `w:3`, a tag,
  `j` and `wtimeout: 1` all succeed with no `writeConcernError`; `w:0` through the driver is
  unacknowledged as expected. This contradicts DECISIONS topic 9, which read `w:2` and above as
  `BadValue` from the engine's main branch: the 1.2.0 gateway does not contain that validation. (The
  managed service does reject them, as DECISIONS predicted; see "Managed service".)
- **Read concerns.** `local`, `majority`, `available`, `linearizable` and `snapshot` are all accepted
  outside a transaction; `available`, `linearizable` and `snapshot` are rejected (115) only as a
  transaction's read concern. No reply carries `operationTime`, `$clusterTime` or `atClusterTime`, so
  causally consistent sessions run without a causal token and snapshot reads cannot be pinned.
  `readPreference: secondary` fails with 133 `FailedToSatisfyReadPreference`; `primaryPreferred`,
  `secondaryPreferred` and `nearest` are accepted.
- **Vector search defaults depend on collection size.** On small collections the engine applied
  `efSearch` equal to the index's `efConstruction` and `nProbes` equal to `numLists`; from about
  10,000 documents `efSearch` defaulted to 40. Explicit values pass through unchanged.
- **Reply shapes.** `createIndexes` nests its counts under `raw.defaultShard` (the gateway answers as a
  sharded router, `hello.msg` is `isdbgrid`), and listed secondary indexes carry an extra
  `storageEngine: { enableOrderedIndex: true }`. That extra option makes Beanie's
  `allow_index_dropping=True` drop and rebuild unchanged indexes on every start; the default `False` is
  a no-op.
- **TTL** purges with a per-minute `pg_cron` job; an array that holds one past Date expires the
  document.
- **Drivers.** `AsyncMongoClient` exists from PyMongo 4.9; Beanie 2.2 needs PyMongo 4.11 or newer
  (not 4.15.0) and no Motor; `pip install "beanie<2"` silently installs Motor 3.7.1, and that stack
  also works against the engine.

The managed-service results follow. Where they differ from 1.2.0, the managed results win.

## Managed service (2026-11-25)

The same areas, plus full-text search activation, Microsoft Entra ID and the CLI, were tested on a
disposable Azure DocumentDB cluster: M30, one shard, server version 8.0, Premium SSD v2, high
availability off, no replica, eastus, created the same day. `hello` reported wire version 25,
`internal.documentdb_versions` `["2.2-1", "2.3.0", "12.1-1"]` and kind `azuredocumentdb`;
`buildInfo` reported 8.0.0. Client: PyMongo 4.20.1, Azure CLI 2.89.1 with documentdb extension
1.0.0. Eight data-plane tests ran in parallel; then the full-text search, Entra ID and CLI tests ran
one at a time, because they change the cluster's configuration. A second agent reviewed each test
against its raw output and judged all eleven sound; where a reviewer found a conclusion broader than
its data, the narrower wording is used here. The upgrade back to 8.0 under a once-a-second probe
(`m-cli-upgrade`, in "CLI and server versions") had no reviewer of its own; its numbers were
re-checked against the raw probe log. The cluster was deleted afterwards. Scripts, reports and
reviews are in `findings/phase4/engine-tests-managed/`. These results are for one cluster shape:
sharded clusters, high availability, replicas, other tiers and older clusters were not tested.

**Same as the open-source engine.** The following matched 0.117 or 1.2.0 with the same code,
codeName and message; differences are listed under the next heading and in the new findings below:

- Vector indexes: one per path (85 for each second index tried against an existing HNSW index,
  including a DiskANN one, which is managed-only: documentdb-local has no DiskANN), the
  identical-repeat no-op, which needs identical options, key order and defaults included (reordered
  keys, or the `m` and `efConstruction` defaults left out, get 86, as on 1.2.0), 86 for the same name
  with other options, the 2,000 and 4,000 caps for HNSW and IVF, the swapped numbers in the IVF
  `numLists` error, and Binary vectors (subtypes 0 and 9) stored but absent from results, with a
  Binary query vector rejected (code 2 "expected an array type field, but received binData").
- **`listIndexes` reports `cosmosSearchOptions` only**, with no `cosmosSearch` key, for every vector
  index listed (HNSW, IVF and half, and the managed-only DiskANN and pq; one HNSW index was also
  listed through the `.global.` host); options under a `cosmosSearch` key in `createIndexes` are
  rejected with 197 ("The field 'cosmosSearch' cannot be used in an index specification"; not tried
  locally). The Learn sample showing `cosmosSearch` is wrong for the managed service; kit helpers
  should read `cosmosSearchOptions`.
- `$jsonSchema`: validators on, `enum` and `oneOf` enforced, the other keywords rejected with code 9,
  a violating insert or update returns write error 121 with no `codeName` or `errInfo`; partial unique
  indexes, `$exists: false` (67) and `sparse` with a partial filter (197) as on 0.117.
- Transactions: 112 `WriteConflict` with no labels, `with_transaction` runs the callback once and
  re-raises, commit is idempotent, 256 after commit, 251 after abort.
- Bulk writes: collection-level `bulk_write` ordered and unordered, `maxWriteBatchSize` 25,000 (this
  settles DECISIONS topic 9 open item 4), PyMongo splits `insert_many` at 25,000, a raw 25,001-op
  insert fails with 16 `InvalidLength`.
- Queries: explain layout, `$setWindowFields` results and `sortBy` codes (5339901, 5339902),
  `allowDiskUse`, and `maxTimeMS` expiry as code 50 `ExceededTimeLimit`, never `MaxTimeMSExpired`.
- TTL: a once-a-minute purge at the top of the minute, so with no backlog a document goes 0 to about
  60 seconds after it becomes eligible (large backlogs were not tested); a compound TTL index is
  rejected (67); of the values tested only BSON Dates (including an array holding a past Date)
  expired.
- Reply shapes: `createIndexes` counts nest under `raw.defaultShard`; no error reply in any of the
  eleven tests carried `errorLabels`.

**Different from documentdb-local (the managed results win).**

- **Snapshot read concern works in transactions.** `startTransaction` with `readConcern: snapshot` is
  accepted and a second read does not see a commit made after the first (seen in two tests;
  documentdb-local rejects snapshot with 115). As on 1.2.0, `available` and `linearizable` are
  rejected with 115 only inside a transaction, and outside one all five levels are accepted. Without
  snapshot, transactions showed the same non-repeatable read and lost update as on 1.2.0.
- **Write concern `w` of 2 or more is rejected** on this cluster with code 2 `BadValue` "w value N
  exceeds the number of data-bearing voting members", and the write is not applied; a tag gets
  `BadValue` "Unknown writeConcern w tag". documentdb-local 1.2.0 accepted both silently. `j` and
  `wtimeout` are accepted with no observable effect.
- **Client-level `bulkWrite` fails at run time.** Because the server advertises wire version 25,
  PyMongo 4.20.1 sends the 8.0 `bulkWrite` command, and the gateway answers code 2 `BadValue`
  "Expected at most one command document and one extra section." (a single-body form gets 59
  `CommandNotFound`). Locally, PyMongo refuses it client-side because the wire version is 21. Other
  drivers were not tried.
- **Causal consistency breaks once a session has an operation time.** Of the replies captured, only
  `hello` and a change stream's own `aggregate` and `getMore` replies carry `operationTime`; write
  replies, `find`, ordinary `aggregate` and `getMore`, and transaction-command replies carry none,
  and no reply carries `$clusterTime`. A PyMongo causal session takes an operation time from any
  reply that carries one (for example `hello` or a change stream run in that session) and from then
  on sends `afterClusterTime`: after a `hello` in the session, or after `advance_operation_time`, the
  find or insert failed with code 20 `IllegalOperation` "readConcern.afterClusterTime is not
  supported on this deployment". `atClusterTime` fails with 72. Outside a transaction, snapshot reads
  carry no `atClusterTime`, so `start_session(snapshot=True)` gives no point-in-time view.
  documentdb-local 1.2.0 gives the same 20 and 72 and no snapshot pinning, but returned no
  `operationTime` in any captured reply, so its causal sessions did not send `afterClusterTime`.
- Present here and missing locally: change streams, full-text search, DiskANN, and MONGODB-OIDC once
  Entra ID is enabled. Before full-text search is enabled, `createSearchIndexes` returns 115 with the
  message "Search index creation is not supported yet" (locally "Command 'createSearchIndexes' not
  supported."). `hello` adds `endpointName` and `operationTime`, explain output adds a top-level
  `instanceName`, and `listCollections` options add `statsEnabled: true`.

**New findings on the managed service.**

*Transactions*

- **A conflict in a snapshot transaction is rolled back, but commit reports success.** When a snapshot
  transaction read a document, another client then updated and committed it, and the transaction
  then updated it, the update failed with 117 `ConflictingOperationInProgress` ("Could not complete
  operation due to conflict with internal apply operation"), with no labels, and `commitTransaction`
  still returned `ok: 1` (4 of 4 runs). None of the transaction's writes were kept, including inserts
  that succeeded before the conflict (all 3 runs that checked). A later insert got 263 ("Operation
  was attempted in a transaction that was aborted"; one run, the only one that sent a statement after
  the 117). Updating a changed document the transaction had not read was not tried. Code that catches
  the 117 and commits gets a success reply for a rolled-back transaction. This looks like a service
  bug to report; until it is fixed, treat 117 as fatal for the transaction and retry the whole
  transaction.
- **Lifetime.** Transactions ended between about 30 and 41 seconds of age whether busy (a write every
  1 s or 5 s) or idle; one busy transaction committed at 40.1 s. Transactions started at different
  times ended at the same instants, about 15 seconds apart, which suggests a periodic sweep (inferred).
  An idle gap of 31 seconds or more makes the next statement fail with code 1 `InternalError` or 251;
  a 25-second idle gap committed. After the first failure, later statements and the commit return
  251 `NoSuchTransaction` and every write is discarded. `getParameter` reports
  `transactionLifetimeLimitSeconds: 30`. Neither error carries a label.
- After a 112 the transaction is gone (commit returns 251, earlier writes discarded); a write error
  inside an `ok: 1` reply (11000, or 14 for `$inc` on a string) was followed by a commit that
  succeeded and kept the earlier writes (one run each; nothing but the commit was sent after the
  error).

*Queries and explain*

- **Whether `COLLSCAN` shows depends on the collection's vacuum state and on the explain verbosity.**
  Just after a 50,000-document load (`collectionPlannerStatistics.allVisibleFraction` 0.0), an
  unindexed find explains as `FETCH` over a bitmap `IXSCAN` on `_id_` at the default, `queryPlanner`
  and `executionStats` verbosities, and as `COLLSCAN` ("Primary Key Scan") only at
  `allPlansExecution`. Once autovacuum has run (`allVisibleFraction` 1.0), the same find shows a root
  `COLLSCAN` at the first three verbosities. When that happened varied and was not controlled: 1.0
  within 20.5 s of loading in one run and within 30.8 s in another, still 0.0 about 26 s after
  loading in a third. Neither `COLLSCAN` nor top-level `totalDocsExamined` is a reliable full-scan
  check: top-level `executionStats` describe only the root stage, and a `LIMIT` root reported 1
  document examined over a scan that examined 12,346. Compare `totalDocsExamined` with `nReturned` on
  the `FETCH` or `COLLSCAN` stage that reports both, not on the top-level totals or a `LIMIT` or
  `SORT` root above it, and not on a bitmap plan's leaf `IXSCAN`, which reports no
  `totalDocsExamined` (for the unindexed range find, the `FETCH` above it showed 50,000 examined for
  45 returned). Treat an `IXSCAN` on `_id_` for a filter that is not on `_id` as a full scan
  (inferred from these plans). Right after a bulk load no plan check is reliable (next point).
- **Before autovacuum, indexed queries appear to have run as full scans.** On the freshly loaded
  collection an indexed equality had full-scan latency and needed a `maxTimeMS` of 16 to 32 ms, while
  its `executionStats` explain showed `IXSCAN` with one document examined; `allPlansExecution`
  showed the full primary-key scan the cursor used. After autovacuum, and with `hint`, it ran at
  `_id`-lookup latency (the link between plan and latency is inferred). Benchmarks and tests that
  query right after a bulk load can measure the wrong plan.
- **PyMongo's `Cursor.explain()` returns no `executionStats` here.** It sends no verbosity, and the
  service answers at `queryPlanner` level (MongoDB's default is `allPlansExecution`). Send the
  `explain` command with `verbosity: "executionStats"` explicitly.
- `maxTimeMS: 1` on `find`: the command failed with 50 before returning anything, except for
  `find({})` and a `batchSize: 1` find, whose first batches were cheap (inferred); the find's
  `maxTimeMS` did not carry over to its `getMore` calls (whether a server default limits a
  `getMore` was not tested), and a `getMore` with `maxTimeMS: 1` and a large batch failed
  with 50 and left the cursor gone.
- The L08 example (two chained cumulative windows, `$set`, `$sort`, `$group` with `$max` and `$last`)
  runs as written and matches a client-side computation (DECISIONS topic 10 open item 2).
- A `$search` cosmosSearch pipeline on IVF explains as `FETCH` with `cosmosSearchCustomParams`
  `{nProbes: 2}` over `IXSCAN` on the vector index, then `LIMIT` and `PROJECT`; no `SORT` or `COLLSCAN`
  (DECISIONS topic 10 open item 3).

*Vector indexes*

- DiskANN works on M30. `createIndexes` accepts `dimensions` up to 2,000 uncompressed and 16,000 with
  `compression: "pq"` (the caps were checked on empty collections; searches used 3 dimensions);
  16,001 fails with 67 "Vector index dimensions cannot exceed the allowed value of 16000", and
  `compression: "half"` on DiskANN fails with 67 "Compression type 'half' is not supported for diskann
  index".
- **New indexes returned complete results at once.** On a 5-document collection an HNSW index returned
  the full result on the first query and on every query for four minutes, and DiskANN and IVF indexes
  returned complete results on the first query; the 2 to 3 minutes of empty results in a Learn
  quickstart's troubleshooting section did not occur at this size (large collections not tested). A
  `$search` on a collection with no vector index fails with code 2 "Similarity index was not found for
  a vector similarity search query." rather than returning nothing.
- **The idempotent repeat needs the same options in the same key order, defaults included.** The same
  values with the option keys in another order, or with the defaults `m: 16` and `efConstruction: 64`
  left out, fail with 86 instead of being a no-op (documentdb-local 1.2.0 gave the same 86). An
  ensure-index helper should send its options in a fixed order with every value explicit, or compare
  against `listIndexes` before creating.

*Schema validation*

- Validators worked on this new cluster with no `previewFeatures` entry, no feature registration and
  no configuration step (DECISIONS topic 10 open item 1, for clusters like this one). A Microsoft Q&A
  thread from May 2026 reported "validator not supported yet" on an 8.0 M20 cluster, so older clusters
  may still be gated.
- A violating `findAndModify` fails with `ok: 0`, code 121, codeName `DocumentFailedValidation`, as
  on documentdb-local 1.2.0 (MongoDB's name is `DocumentValidationFailure`): match on the code.
- `title` and `description` are accepted (`title` was tried only at the top level); `$schema`,
  `format` and `type: "integer"` fail with 9 ("is not supported at this time"). Generated schemas, for
  example from Pydantic or zod, also tend to contain `anyOf` and `additionalProperties`, which are
  rejected, so they need translating rather than passing through.
- `validationAction: "warn"` accepts a violating write, as on documentdb-local 1.2.0. The open-source
  engine's source code skips validation entirely in that mode, so the violation is probably not logged
  either; don't use `warn` to audit.

*Change streams* (one shard, no feature enabled)

- `collection.watch()` works with no enablement step and delivered events about 0.3 s after the
  writes. Events carry `_id`, `operationType`, `wallTime`, `documentKey` and `ns`, plus `fullDocument`
  on inserts and updates (not on deletes), and no `clusterTime`; a `replace` is reported as `update`.
- **Update events never carry `updateDescription`**, by default, with `updateLookup`, or after
  `collMod {enableUpdateDescription: true}` (which is accepted). Learn's form
  `{enableUpdateDescription: {enabled: true}}` fails with 14 `TypeMismatch`. Every update event carries
  `fullDocument` as of that update, with or without `updateLookup`.
- **`db.watch()` opens but delivered no event** in five tests; `client.watch()` delivered events from
  the test database (other databases were not written while it was open). Use collection streams.
- `resume_after` and `start_after` replayed the events missed while the stream was closed, in order and
  without duplicates; `start_at_operation_time` works, and times before the cluster existed are
  accepted. Write replies carry no `operationTime`, so a start time has to come from the
  `operationTime` of `hello` or of a change stream's own `aggregate` and `getMore` replies (ordinary
  `find`, `aggregate` and `getMore` replies carry none), or from an event's `wallTime`.
- Token errors, all without labels: 2 `BadValue` "Resume token is invalid" (or "Encoded Resume token is
  invalid") for malformed tokens; 40647 `ChangeStreamBadResumeToken` when `_data` is missing or not a
  string; 14 when `resumeAfter` is a string; 72 `InvalidOptions` "Expired resume token or cursor,
  reinitialize the change stream cursor" for fabricated very old positions, 1 and 10,000,000 (not 286
  `ChangeStreamHistoryLost`). An accepted token does not prove a working stream: position 100,000,000
  was accepted, but one 2-second `getMore` returned nothing and `postBatchResumeToken` did not move,
  while 170,000,000 replayed the collection's events. A corrupted token that points ahead of the log
  gives a silently idle stream.
- **Dropping a watched collection or database sends no `drop` or `invalidate` event.** The server kills
  the cursor (43 `CursorNotFound`) and PyMongo resumes silently, so the stream keeps running on the
  recreated collection. Tokens are not bound to a collection, and the same change has different `_id`
  values in different streams (its `wallTime` was the same in each): an event `_id` is a stream
  position, not an id to de-duplicate on.
- Pre-images work after `collMod {changeStreamPreAndPostImages: {enabled: true}}`; with
  `fullDocumentBeforeChange: "required"` on a collection without them, the update itself succeeds,
  but the stream's next `getMore` fails with 10065 and the cursor is gone. `showExpandedEvents` fails
  with 115.

*Hosts and connection strings*

- Each host has one SRV record (port 10260, TTL 30 s) pointing at a node name
  `fc-<id>-000.mongocluster.cosmos.azure.com` or `fc-<id>-000.global.mongocluster.cosmos.azure.com`;
  there are no TXT records. The cluster hosts have no A record, so a `mongodb://` string with the
  cluster host fails; a tool that cannot use SRV needs the node name, which no service-issued string
  contains (whether node names stay the same through scaling, high availability, maintenance or a
  replica promotion was not tested). A third node name,
  `fc-<id>-000.ro.global.mongocluster.cosmos.azure.com`, appears in the certificate and accepts logins.
- **The `.global.` host resolves and authenticates on a single cluster with no replica**, and writes
  through either host are visible through the other.
- `list-connection-strings` returns `GlobalReadWrite` first and `Self` second; with Entra ID enabled
  it adds `GlobalMicrosoftEntraId` and `MicrosoftEntraId`, both with `authMechanism=MONGODB-OIDC` and
  no credentials. `properties.connectionString` stays the Self SCRAM string. Every service-issued
  string carries `retrywrites=false&maxIdleTimeMS=120000`.
- PyMongo prints its "You appear to be connected to a CosmosDB cluster" warning for any
  `*.cosmos.azure.com` host, twice for the first `mongodb+srv` client in a process.
- `getParameter: "*"` returns eight parameters, including `transactionLifetimeLimitSeconds: 30`;
  `getParameter` for `featureCompatibilityVersion` fails with `ok: 0` and "No option found for get",
  with no code.

*Read and write concerns* (all as on documentdb-local 1.2.0)

- `w: 0` through the driver is unacknowledged and reports no duplicate-key error; a raw command with
  `w: 0` still gets a full reply.
- `readPreference: secondary` fails with 133 `FailedToSatisfyReadPreference`; the one tag set tried
  (`[{dc: "east"}]` with `secondaryPreferred`) fails with 133, `hedge` with 2 ("hedged reads are not
  supported"), and `primary` with `maxStalenessSeconds` with 9.
- `getDefaultRWConcern` returns the constant majority/majority document (admin only; elsewhere 13
  `Unauthorized`); `setDefaultRWConcern` returns 59 `CommandNotFound`.

*Full-text search activation*

- Learn's `az rest` PATCH of `properties.previewFeatures` returned in under a second; the cluster read
  `Updating` for 150 to 180 seconds. **`createSearchIndexes` returned 115 "Search index creation is not
  supported yet" for the first 90 seconds, then 67 `CannotCreateIndex` with the same message, and
  succeeded at 210 seconds**, 0 to 30 seconds after `provisioningState` first read `Succeeded`. Retry
  on that message under either code, with Learn's ten minutes as an upper bound: a cluster where the
  preview was never enabled returns the same 115 and message, so an unbounded retry never ends. The
  full ten minutes were not needed here (one observation).
  Existing connections kept working; no reconnect was needed.
- `$listSearchIndexes` started answering (with an empty list) a minute or more before index creation
  worked, so it is not a readiness check. After creation the index was `READY` and `queryable: true` on
  the first listing (3 documents).
- `$search` with `text` returns BM25 scores; `compound` with `must`, `should`, `filter` and `mustNot`
  returns the result Learn states; `compound.minimumShouldMatch` and `$searchMeta` fail with 115;
  `$rankFusion` with 40324; Learn's `$unionWith` RRF hybrid pipeline works in one round trip and
  matches a client-side RRF.
- `dropIndexes` drops a search index; `dropSearchIndex` and `updateSearchIndex` return 59
  `CommandNotFound`, which is what PyMongo's `drop_search_index` and `update_search_index` send.
  `mappings.dynamic: true` fails with 67 `CannotCreateIndex` "Error in specification
  {...}:mappings.dynamic is not supported in search indexes yet" (Learn quotes it without the prefix).
  `listIndexes` omits search indexes, but index counts include them. `$search` output without a
  `$project` carries an internal `__cosmos_meta__: {score}` field.

*Microsoft Entra ID*

- `az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID` (extension
  1.0.0) took 155 seconds; SCRAM logins kept working, and `hello.saslSupportedMechs` gained
  `MONGODB-OIDC`.
- `az documentdb mongocluster microsoft-entra-user assign --type` accepts `User` and
  `ServicePrincipal` only. A personal Microsoft account that is a member of its own directory was
  registered as administrator, and its first OIDC login worked 8 seconds later.
- Errors, all code 18 `AuthenticationFailed` without labels: Entra ID not enabled, "The authentication
  mechanism provided is not supported in the service."; identity not registered, "External identity is
  not present in the system."; no token in `saslStart`, "JWT token missing from OIDC payload". The
  server never returned identity-provider information, so only one-step token flows are likely to work
  (inferred).
- **PyMongo floors with Learn's custom callback:** 4.6.3 cannot use a callback at all; 4.7.0 and 4.10.1
  refuse the Azure host before calling the callback unless `ALLOWED_HOSTS` is set (that the releases
  in between do the same comes from a reading of their source that was not captured raw), and 4.7.0
  with `ALLOWED_HOSTS` connects; 4.11 (plain host) and 4.20.2 (plain and `.global.` hosts) connect
  without it. So the floor is 4.11 without `ALLOWED_HOSTS` and 4.7.0 with it. Learn's Python sample
  sets no `ALLOWED_HOSTS` and therefore needs 4.11 or later (inferred: the runs used
  `AzureCliCredential`, and 4.11 ran only on the plain host, while the sample uses
  `DefaultAzureCredential` and the `.global.` host; neither difference matters to a check that runs
  before the callback and whose default list has no Azure domain).
- **Node.js:** 6.6.0 rejects `OIDC_CALLBACK`; 6.7.0 and 7.9.1 connect, but only with `ALLOWED_HOSTS`,
  because the default lists contain no Azure domain. Both `['*.azure.com']` and
  `['*.mongocluster.cosmos.azure.com']` work.
- The administrator appears in the database as user `<object-id>` in `admin` (not `$external`) with
  role `root` and `customData.IdentityProvider.type` `MicrosoftEntraID`; `usersInfo` with `db:
  "$external"` fails with 2 ("Only 'admin' is allowed.").

*CLI and server versions*

- **A downgrade was accepted in one test.** `az documentdb mongocluster update --server-version 7.0`
  on the 8.0 cluster exited 0 after 94 seconds with no warning; `hello` then reported wire version 21
  and `buildInfo` 7.0.0, with the same engine build. Upgrading back to 8.0 took 128 seconds, and 145
  once-a-second probes (`hello`, an insert and a count) spanning the change all succeeded; the wire
  version switched to 25 about 90 seconds in (this upgrade probe had no separate reviewer; its raw log
  is `m-cli-upgrade/pings.jsonl`). The `--server-version` help warns of nothing and says it "Defaults
  to the latest available version if not specified". On `update` that is wrong: in the extension 1.0.0
  source, `update` reads the cluster and PATCHes the current body back, so leaving the flag out keeps
  the current version (read from the source, not observed; the m-entra `update` that left 8.0 in place
  ran while 8.0 was also the latest version). The `update` output still reads `Updating`; poll `show`
  until `Succeeded` and `Ready`.
- **Dynamic extension install:** with no TTY, the first `az documentdb ...` command in a fresh
  configuration installs the latest stable documentdb extension (1.0.0 on that day) without asking
  and re-runs the command; with a TTY it stops at a "(Y/n)" prompt, and answering n exits 2. Scripts
  should run `az extension add --name documentdb` first.
- Whether new clusters accept server versions 5.0 and 6.0 was not tested: creating the extra test
  clusters was refused by local permissions (DECISIONS topic 11 open item 3 stays open).
