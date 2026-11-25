# Engine tests against documentdb-local

Open questions that depend on engine behaviour were tested on this Mac against the open-source
engine, image `ghcr.io/documentdb/documentdb/documentdb-local`, as pulled locally on 2026-09-25:
OCI version 0.117.0, revision 28cc0120, PostgreSQL 17.11, pgvector 0.8.6, wire version 21 (the
gateway advertises MongoDB 7.0.0). Note that the `latest` tag has since moved to engine 1.2.0;
these results are for 0.117 and should be rerun on 1.2.0 before being quoted (see "Rerun" below).
Everything here is evidence about the open-source engine and gateway, not proof of managed-service
behaviour. Scripts and JSON reports with every raw response are in `findings/phase4/engine-tests/`.

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
  service before the kit's ensure-index helper relies on one key. The kit helper should read both.
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
  the managed service runs that build is the remaining question.
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
  first operation.

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
  `totalDocsExamined` against `nReturned` is the reliable signal.
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

## Rerun

The results above are for engine 0.117. The `write-read-concerns` test did not run. Rerun all ten on
`pg17-1.2.0` with a fresh container before quoting any of them, and compare the `listIndexes` key,
the `$jsonSchema` keyword set, the snapshot read concern and the transaction error labels, which are
the items most likely to have changed.
