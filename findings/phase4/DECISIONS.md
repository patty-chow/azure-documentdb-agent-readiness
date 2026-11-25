# Phase 4 decisions and answered questions

## retryWrites: answered 2026-11-25

**Answer.** `retrywrites=false` is required, not a style choice. Azure DocumentDB does not support
retryable writes. The DocumentDB product team confirmed this in an internal sync on 2026-11-23 and is
changing every sample in Learn and the Azure-Samples repositories to `retrywrites=false`; by
2026-11-25 the TypeScript and .NET Learn samples were consistent. The kit's own
`skills/azure-deployment/SKILL.md` (line 291) already says the feature is not supported, while three
other kit files still show `retryWrites: true` (`skills/connection/SKILL.md:60`,
`skills/driver/driver-singleton-client.md:26`, `skills/security/security-tls-required.md:26`).

**Mechanism, from the engine.** Open issue documentdb/documentdb#767 (filed 2026-10-05): the gateway
passes a NULL transaction id to the engine, so the engine's retryable-write de-duplication table is
never used; sending the same `lsid` + `txnNumber` twice applies the write twice. A driver with
`retryWrites=true` therefore gets no exactly-once protection: a retried non-idempotent write (for
example `$inc`) can be applied twice, and a retried insert reports a duplicate key for a write that
succeeded. That is the concrete risk behind "not supported".

**What is not established.** No source shows that `retryWrites=true` by itself produces connection
errors, which is what the kit's azure-deployment sentence claims. Filings must not assert that.

**What Learn says today.** Every quickstart and the Entra ID page carry `retrywrites=false` in the
connection string, but no Learn page (limitations, compatibility, connect) explains why. That gap is
part of the Learn filings L03 (write semantics) and L07 (connection-string reference) as a concrete
ask rather than a question.

**Canonical one-liner for the kit and samples.**
"Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support
retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a
non-idempotent write twice. Handle transient write failures in application code with idempotent
operations (upserts, deterministic keys)."

Sources: DocumentDB product team, internal sync 2026-11-23 and follow-up 2026-11-25;
https://github.com/documentdb/documentdb/issues/767;
https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs;
https://learn.microsoft.com/en-us/azure/documentdb/limitations;
https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language.

## Vector indexes (SME topic 6): settled from the docs on 2026-11-25, two items still open

**Settled, cite these pages, no SME needed.**

- Parameter ranges and defaults, all from the vector search page
  (https://learn.microsoft.com/en-us/azure/documentdb/vector-search, per-algorithm tabs): HNSW `m` 2 to 100
  (default 16), `efConstruction` 4 to 1000 and at least 2m (default 64), `efSearch` default 40; IVF
  `numLists` = documentCount/1000 up to 1M documents, start at 1 for demos, `nProbes` default 1 and at
  most `numLists`; DiskANN `maxDegree` 20 to 2048 (default 32), `lBuild` 10 to 500 (default 50),
  `lSearch` 10 to 1000 (default 40) with `k` at most `lSearch`.
- Dimension limits, from three pages that agree: 2,000 without compression; 4,000 with
  `compression: "half"` on HNSW or IVF; 16,000 with product quantization on DiskANN
  (vector-search "Features and limitations"; https://learn.microsoft.com/en-us/azure/documentdb/half-precision;
  https://learn.microsoft.com/en-us/azure/documentdb/product-quantization;
  https://learn.microsoft.com/en-us/azure/documentdb/limitations). Filings quote these numbers.
- Build order: HNSW can be created on an empty collection (vector-search, HNSW column); IVF `numLists`
  depends on document count, so create or re-create it after loading; a product-quantization index
  should be created after the collection has data (product-quantization page, note). A new index can
  return empty results for 2 to 3 minutes while it builds
  (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-select-algorithm, Troubleshooting).
- One index per path: "Indexing applies to only one vector per path. You can create only one index per
  vector path." (vector-search features list and the limitations page). The quickstart's narrower
  code comment ("no two vector indexes of the same kind on the same field") is treated as imprecise.
- `listIndexes` reports the options under `cosmosSearch` (vector-search, "Get vector index definitions").
- BSON binary vectors: Learn requires an array of numbers and says a document whose vector has another
  type is not indexed and is silently absent from results (vector-search, DiskANN field table and IVF
  Important box). Engine issue documentdb/documentdb#109 (closed completed 2026-04-28) confirms
  DocumentDB 0.110 stores and returns BSON binary subtype 9 intact, and its closing comment states that
  index-side search on subtype-9 fields is a separate, untracked feature. The experiment observed the
  same: binary vectors inserted, never returned, and a binary query vector rejected with "expected an
  array type field". Filings may state the exclusion as fact and ask Learn to name binary explicitly.

**Still open for engineering.**

1. HNSW dimension limit. The select-algorithm quickstarts
   (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-select-algorithm and the
   Python variant) say HNSW supports up to 8,000 dimensions; the concept, half-precision and
   limitations pages say 2,000 uncompressed and 4,000 half-precision. Which is current? Filings use
   2,000/4,000 and flag the quickstart figure as a doc inconsistency.
2. IVF above one million documents. The vector-search IVF field table says `numLists` =
   sqrt(documentCount) above 1M; the Important box under it says to use DiskANN instead. Filings follow
   the Important box.

**Not an SME item.** The error returned for a same-name index with different options, and whether an
identical `createIndexes` call is a no-op, are undocumented; filings describe the ensure-index helper as
tolerant of both outcomes rather than asserting a code.
