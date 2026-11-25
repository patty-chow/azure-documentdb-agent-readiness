# Questions for the Azure DocumentDB engineering and docs owners

Distilled from the open-question sections of the 43 phase-4 filings (`findings/phase4/filings/`). Each
block lists the filings that cannot go public until it is answered. One answer per block clears every
filing that cites it. Decisions that belong to a repository maintainer rather than a service SME are at
the end.

## 1. retryWrites. ANSWERED 2026-11-25, see DECISIONS.md (was blocking 17 filings: K01, K03, K04, K07, K10, K11, K23, K27, K34, L01, L02, L03, L04, L05, L06, L07, L11, H07)

The published connection string sets `retrywrites=false`. Two positions circulated in the drafts:
(a) retryable writes are not supported and leaving the driver default on causes connection or write
errors (the kit's `azure-deployment` skill says this); (b) Learn never states they are unsupported, and
the Mongoose tutorial calls the value a sample choice. Which is right? Is `retrywrites=false` required,
recommended, or optional, and what one-line rationale should the kit and Learn give?

## 2. Throttling and transient errors (K07, K23, K32, L03, L04, H07)

Does Azure DocumentDB ever return error 16500 or HTTP-429-style throttling to a MongoDB client, or only
timeouts and latency? Which error codes does a client see during HA or cross-region failover (10107, 189
stepdown, or network errors only)? Does the engine return the `TransientTransactionError` and
`UnknownTransactionCommitResult` labels that drivers' `withTransaction` retry relies on (also L08)?

## 3. Host forms (K01, K03, K10, L05, L06, L07)

Learn shows both `<cluster>.mongocluster.cosmos.azure.com` and `<cluster>.global.mongocluster.cosmos.azure.com`.
When is the `.global.` host required (clusters with a cross-region replica only?), and does the plain
host work for a single cluster? Should guidance say "keep whichever the portal gives"?

## 4. Driver and ODM version floors (K03, K07, K20, L01, L05, H11)

Minimum driver versions for `MONGODB-OIDC` (drafts cite PyMongo 4.7 and Node `mongodb` 6.7; Java and
.NET unknown). The PyMongo floor for `AsyncMongoClient` (4.9 beta, 4.11, or 4.13 GA). Whether the kit
should recommend Beanie 2.x on `AsyncMongoClient` and mark Beanie 1.x + Motor as not recommended; the
correct Motor deprecation and end-of-life dates. Minimum driver version per language for server
versions 5.0 to 8.0, and whether Node 24 is tested. Tested pins for the LlamaIndex, Java, .NET, Go and
Rust quickstarts. Should any skill state version minimums at all?

## 5. Microsoft Entra ID specifics (K03, L05, L07)

Must `readWriteAnyDatabase` and `clusterAdmin` be granted together for non-admin Entra identities, or
are they separate roles? Accepted `--type` values for `az documentdb mongocluster microsoft-entra-user
assign` (User, ServicePrincipal, managed identity?). `ALLOWED_HOSTS` for the OIDC callback: `*.azure.com`
(Learn) or `*.mongocluster.cosmos.azure.com` (MCP repo)? Terraform: is `authConfig.allowedModes` exposed
in `azurerm_mongo_cluster` 4.x, or is `azapi` the route? Is there a verified Java OIDC callback? Learn's
TypeScript sample appears to mix seconds and milliseconds in `expiresInSeconds`; is it wrong? Can a
non-admin user run `connectionStatus` with `showPrivileges` and `usersInfo` on itself; are custom roles
still preview?

## 6. Vector indexes (K05, K23, L02, L09, M01). SETTLED 2026-11-25 (Learn pages; HNSW limit confirmed by the product owner: 2,000/4,000, the quickstarts' 8,000 is wrong), see DECISIONS.md; only the numLists guidance above 1M documents remains open

Confirm HNSW and IVF parameter ranges and defaults (`m` 2 to 100, default 16; `efConstruction` 4 to 1000,
default 64, at least 2m; `efSearch` 40; IVF `numLists` up to 1M; `nProbes` default 1), and the dimension
limits: quickstarts say 8,000 for HNSW, concept pages say 2,000 uncompressed, 4,000 half-precision and
16,000 with product quantization. Should IVF be built after loading data or on an empty collection
starting with `numLists: 1`? Does `listIndexes` report options under `cosmosSearch`, `cosmosSearchOptions`
or both? Is "one vector index per path" current? What does a same-name index with different options
return, and is an identical `createIndexes` a no-op? Can a new index return empty results while it builds,
and for how long? Are BSON Binary vectors definitely not indexed, and is the "expected an array type
field" error worth documenting? Is the MCP README's minimal `vector-hnsw` example valid as written?

## 7. Full-text and hybrid search status (K05, K17, K22, K23, L02, L09). SETTLED 2026-11-25 except whether code 115 also appears during activation, see DECISIONS.md

Is full-text search (`createSearchIndexes`, `$search`) still preview with the `FullTextSearch` preview
feature and a roughly 10-minute activation, or GA? Is `CommandNotSupported` (code 115, "Search index
creation is not supported yet") the intended error when it is off and during activation? Is `$search`
`compound` available now (the kit says no, Learn's overview lists it)? Are text and vector indexes free
on every tier with no SKU restriction? Learn's hybrid-search tuning text says a larger k for the keyword
arm while its example uses the smaller one: which is right? `compatibility-query-language` marks
`$listSearchIndexes` unsupported while the search pages use it: which is correct?

## 8. Change streams (K04, K07, K32, L03, L09)

Is the active change log 400 MB, and is that where `resumeAfter` stops working? Do historical streams
reach back up to 35 days through point-in-time restore? Can multishard change streams still not be
enabled together with the multishard rebalancer? Are multishard change streams and `updateDescription`
still preview? Do single-shard clusters need no enablement step? What error does the service return for
a token that can no longer be resumed? Is there a CLI, ARM or Bicep property for the multishard toggle?
Is `fullDocument: 'updateLookup'` supported on all tiers?

## 9. Transactions, write semantics and bulk operations (K07, L03, L04, L08)

Are multi-document transactions supported across shards, with the same 30-second lifetime, and are
there limits on operations, documents or size per transaction? Which `w`, `j`, `wtimeoutMS`,
`readConcern` and `readPreference` values are honored, with and without HA, and what are the defaults?
Does the compatibility page's `bulkWrite: No` refer only to the MongoDB 8.0 server-level command, with
collection-level `bulkWrite()` working in current drivers? Is there any server-side `_etag` or
concurrency token? Recommended starting batch sizes per M-series tier; are foreground unique-index
builds and the `blocking: true` option current for all server versions?

## 10. Schema validation, TTL, indexing and query behaviour (K11, K32, L08, L10)

Does `$jsonSchema` support `enum`, `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`,
`patternProperties` and `dependencies` today? Is `{ unique: true, partialFilterExpression: { key: { $exists: true } } }`
accepted? TTL semantics: single-field only, non-Date values ignored, handling of a missing field, deletion
lag (about 60 seconds?). Does `allowDiskUse` change behaviour or is it a no-op? Does the suggested
`$setWindowFields` example (chained stages, `$last` in `$group`, cumulative `documents` window) run? Is
`sortBy` required for every window except unbounded? Is 120 seconds the default query execution limit?
Is the claim that wide rows are detoasted on read before projection accurate and worth stating? Does
checking for `COLLSCAN` anywhere in explain output work with DocumentDB's explain layout? Confirm
monitoring facts: diagnostic logs unavailable on M30 and lower and free tiers; the `vCoreMongoRequests`
category and table; metric names `CpuPercent`, `MemoryPercent`, `StoragePercent`, `IOPS`.

## 11. CLI, IaC and server versions (K20, K34, X01, H09, H11)

Is `az cosmosdb mongocluster` (cosmosdb-preview) deprecated or only superseded by `az documentdb
mongocluster`, and is a deprecation redirect the owners' plan? Are both groups still preview, and is
Azure CLI 2.75.0 the right minimum for the `documentdb` extension? Does first-use dynamic extension
install prompt in non-interactive shells? Can clusters created with the old group be managed with the new
one? Which `--server-version` values are accepted at create time (5.0, 6.0, 7.0, 8.0), is 8.0 the right
default, and can a cluster's major version be upgraded in place? Exact JSON paths in `az documentdb
mongocluster show` output for `serverVersion`, `compute.tier`, `sharding.shardCount`,
`authConfig.allowedModes` and `highAvailability.targetMode`. Does Azure CLI compile Bicep on the client?
Billing facts to confirm: per-shard, per-hour compute, storage grows but does not shrink, Free tier, M25
burstable.

## 12. Local gateway container (H03, K23, K27, L11)

Does the `documentdb-local` image support `cosmosSearch` indexes (all three kinds), `createSearchIndexes`
and `$search`, transactions, change streams and Entra ID like the managed service? Which versioned tag
should CI pin instead of `:latest`? Should the canonical local URI carry `authMechanism=SCRAM-SHA-256`
explicitly? Should the `microsoft/documentdb-mcp` README use the 10260 gateway example instead of
localhost:27017?

## 13. Encryption, compliance and framework integrations (K03, K27, K30)

Are client-side field-level encryption (explicit and automatic) and Queryable Encryption supported? Is
pointing PHI workloads at an Azure OpenAI or Foundry deployment acceptable wording with no compliance
claim? Is `documentdb-mcp-server` published on npm (the kit's `mcp.json` runs it with `npx`; Learn says
no package yet)? Does the Azure MCP Server plan a DocumentDB namespace? Is "Azure DocumentDB MCP Toolkit"
the canonical product name? Which LangChain Python package should the kit recommend,
`langchain-azure-cosmosdb` or `langchain-azure-ai`? Is there a LlamaIndex TypeScript vector store for
DocumentDB? Does the LlamaIndex 0.9.0 behaviour (constructor creates an HNSW index, `pre_filter` instead
of `MetadataFilters`) still hold?

## Not SME questions: maintainer decisions

- Kit (K05, K07, K10, K13, K23, K25, K27, K34, K36): split the indexing half of the vector-search PR;
  pool defaults 50/5 or 20/0 and `DOCUMENTDB_*` or `DB_*` names; default model names in `.env.example`;
  `VERSION` 0.1.0 or 0.2.0; `allowed-tools: mcp__documentdb__*` on general skills; CLI before portal in
  Step 8; bulk-load rule in `driver` or `local-deployment`; install-script URI edits now or later.
- MCP server (M01): hide tools whose tier is off from `tools/list`, or keep the description note; move
  `create_index` to the write tier.
- Harness (H01 to H12): intent of the experiment (management and write tools on or off); keep
  `max_consecutive_errors_per_request=10` upstream or fork-only; `run_policy` as a `ReasonSource`; pin
  Python 3.12; where shared prompt blocks live; LLM defaults for builders; re-baseline runs before quoting
  any sample count externally.

## Caution carried in every filing

All sample counts come from one run of 100 prompts whose harness had defects now identified (MCP flags
off, installed kit reported missing, empty builds graded, Python 3.13 install failures). The filings say
so. Re-run after the harness fixes before quoting counts outside the team.
