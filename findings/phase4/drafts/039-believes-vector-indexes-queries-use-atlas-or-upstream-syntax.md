---
title: "vector-search skill: state that vectors must be stored as number[] (BSON Binary embeddings are not indexed)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 69
findings: 90
bucket: confusion-sample-specific
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# vector-search skill: say that vectors must be stored as `number[]` (BSON Binary embeddings are not indexed)

## What happens today

`skills/vector-search/` corrects the Atlas/upstream priors an LLM brings to vector search: `vector-knn-query.md` labels `$vectorSearch` "not supported in DocumentDB" and shows `$search` + `cosmosSearch`; `vector-create-diskann-index.md` shows `createIndex` + `cosmosSearchOptions` with `dimensions: 1536 // matches text-embedding-3-small`; and the separate `skills/full-text-search/fts-create-search-index.md` says full-text search indexes use `createSearchIndexes`, not a `text` key. That works: in an experiment that built 100 Azure DocumentDB sample apps with gpt-5-mini and this kit installed, 90 cold-quiz findings across 69 samples showed Atlas/upstream priors; 87 of them reached for `knnVector`, `$vectorSearch`, `createSearchIndexes` for the vector index, or `$text`, and once the skill loaded the builds used the `cosmosSearch` forms. No change is needed for that.

The one thing no file in `skills/vector-search/` mentions is the **storage type of the embedding field** (`grep -riE 'binary|number\[\]|array' skills/vector-search/` matches only a `.toArray()` call in `vector-knn-query.md`). Azure DocumentDB only indexes vectors stored as a plain `number[]`. Microsoft Learn says so twice on https://learn.microsoft.com/en-us/azure/documentdb/vector-search: "Vectors must be a `number[]` to be indexed... A vector using another type, such as `double[]`, prevents the document from being indexed. Nonindexed documents aren't returned in the result of a vector search." Learn does not name BSON Binary explicitly, but a Binary (packed float32, e.g. subtype 0x09) field is "another type", so those documents are left out of `$search` results without an error at insert or index-creation time. An agent that trusts the skill and does not open the Learn page never sees this rule.

## Why it matters

Three of the 100 sample prompts asked for embeddings "stored as BSON binary vectors" (an Atlas BinData-vector idiom). In 4 of the 5 builds of those prompts the agent, with this skill loaded, packed the floats into `bson.Binary` and shipped a sample whose server-side vector search does not work as intended:

- `01-product-catalog-with-vector-search` (two runs): the app stores `Binary(struct.pack(...))`; the audit notes this prevents the server-side vector index from working as the README intends, and the `/search` route falls back to unpacking the Binary and ranking client-side.
- `11-visual-similarity-search-image-embeddings` (two runs): `scripts/seed.py` line 54 stores `bson.Binary(vec.tobytes(), subtype=0x09)`; the audit records an "Invalid type: expected an array type field" error during the build's `$search` attempts (alongside an unrelated "$search must be the initial stage" error), and the second run fell back to client-side cosine.
- Only `04-medical-imaging-metadata-store` caught it, because the readiness step happened to read the Learn page; it marked the build "blocked" and switched to `number[]`.

So the skill currently fixes every syntax-level Atlas prior but lets through the one data-level prior that produces a sample which looks correct, creates its index without error, and returns no indexed results.

## Proposed change (two files, ~10 lines)

**1. `skills/vector-search/vector-normalize-embeddings.md`**: add a rule bullet next to the existing model + dimensions guidance and an Incorrect/Correct pair:

```markdown
Rules:
- ...
- Store the **embedding model name** and **dimensions** alongside the vector ...
- Store the vector itself as a plain array of numbers (`number[]`). BSON Binary /
  packed-float32 vectors (Atlas "BinData vector" style) are **not indexed** by
  `cosmosSearch`; those documents are left out of every `$search` result.
```

Incorrect:

```python
# Packing floats into BSON Binary -> document is not indexed, $search never returns it
doc["embedding"] = bson.Binary(np.asarray(vec, dtype=np.float32).tobytes(), subtype=0x09)
```

Correct:

```python
doc["embedding"] = [float(x) for x in vec]   # number[]; this is what cosmosSearch indexes
```

**2. `skills/vector-search/SKILL.md`**: extend the rule-list line (currently line 26) so the rule is visible without opening the file:

```markdown
- [vector-normalize-embeddings](vector-normalize-embeddings.md) — Normalize embeddings when using cosine similarity; store model + dimensions alongside vectors; store vectors as `number[]`, never BSON Binary.
```

Optional: add one row to the four-column parameter table in `vector-create-diskann-index.md`, since that is the file agents open when writing the `createIndex` call:

```markdown
| Field type | `number[]` | — | BSON Binary / other types are not indexed; those documents are excluded from `$search` |
```

No Learn-docs change is proposed; the page already carries the rule (naming BSON Binary next to `double[]` there would be a nicety).

## Evidence (run folders from the experiment)

- `runs/01-product-catalog-with-vector-search/20261124-175429/`: `05-audit.json`, `doc-gaps.md` "Embedding storage type and indexing", `app/app.py`, `app/scripts/load_data.py`
- `runs/01-product-catalog-with-vector-search/20261125-061803/`: `app/utils.py` (`floats_to_bsonbinary`), `05-audit.json` summary
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/`: `app/scripts/seed.py` line 54, `05-audit.json` ("Invalid type: expected an array type field")
- `runs/11-visual-similarity-search-image-embeddings/20261125-061803/`: `app/app/db.py` (`pack_embedding`), `05-audit.json`
- `runs/04-medical-imaging-metadata-store/20261124-193446/`: `02-readiness.json` verdict "blocked" and information gap "Embedding storage precision vs index method"

## Verification

### 1. Already covered? confirmed (not in the kit; documented on Learn)

- Agent Kit: `grep -rniE 'binary|number\[\]|bindata|float32' skills knowledge-base` finds no vector storage-type guidance (only unrelated hits in `skills/natural-language-querying/SKILL.md`). `skills/vector-search/vector-normalize-embeddings.md` rules cover similarity, normalization and storing model name + dimensions only. `skills/vector-search/SKILL.md` line 26: "Normalize embeddings when using cosine similarity; store model + dimensions alongside vectors." `vector-half-precision.md` covers fp16 index storage (`halfPrecision: true`), not the document field type.
- documentdb-mcp: grep for `bson binary|number[]|bindata|binary vector` finds nothing (the MCP server is not the right place for this anyway).
- Learn (https://learn.microsoft.com/en-us/azure/documentdb/vector-search) already states the rule in the DiskANN field table and in an Important callout under IVF. So the gap is specifically in the kit, which is where the agent looked.

### 2. Premise true? confirmed (with wording corrections applied)

- Learn: "Vectors must be a `number[]` to be indexed and used in vector search results. A vector using another type, such as `double[]`, prevents the document from being indexed. Nonindexed documents aren't returned in the result of a vector search." Matches the task's authoritative fact that BSON binary vectors are not indexed.
- The kit claims hold: `vector-knn-query.md` line 11 "Using Atlas Vector Search syntax (`$vectorSearch`) — not supported in DocumentDB"; `vector-create-diskann-index.md` line 39 `dimensions: 1536, // matches text-embedding-3-small`; `skills/full-text-search/fts-create-search-index.md` line 7 search indexes use `createSearchIndexes` "not `createIndexes` with a `"text"` or `"textSearch"` key type".
- Run evidence spot-checked: `runs/11-visual-similarity-search-image-embeddings/20261124-184225/app/scripts/seed.py:54` is `p["embedding"] = bson.Binary(vec.tobytes(), subtype=0x09)`; its `05-audit.json` records the "Invalid type: expected an array type field" error alongside a "$search must be the initial stage" error.
- Corrections applied to the body: (a) Learn names `double[]` as its example, not BSON Binary, so the body now says Binary falls under "another type" instead of implying Learn names it; (b) the draft's grep claim said it "finds nothing", but `array` matches a `.toArray()` call, now stated precisely; (c) the error in sample 11 is attributed as the audit records it, not as a proven single cause; (d) counts reworded to 90 findings across 69 samples (87 syntax priors + 3 storage/dimension), verified against the findings records; (e) `fts-create-search-index.md` lives in `skills/full-text-search/`, not `skills/vector-search/`; (f) the optional DiskANN table row now matches the table's four columns; (g) nested code fences flattened so the Markdown renders.

### 3. Maintainer skeptic: confirmed

Names exact files (`skills/vector-search/vector-normalize-embeddings.md`, `skills/vector-search/SKILL.md`, optionally `vector-create-diskann-index.md`), gives the exact lines to add, is Azure DocumentDB-specific (cosmosSearch indexes only `number[]`), is consistent with the official Learn page, and fixes a failure mode seen in builds. As a kit maintainer I would accept this PR with at most wording edits. It belongs in Azure/documentdb-agent-kit.

## Finding ids

- F0012
- F0049
- F0050
- F0080
- F0082
- F0121
- F0188
- F0222
- F0324
- F0394
- F0430
- F0504
- F0505
- F0534
- F0564
- F0565
- F0606
- F0609
- F0637
- F0639
- F0668
- F0704
- F0607
- F0120
- F0608
- F0734
- F0772
- F0857
- F0978
- F0979
- F1008
- F1112
- F1171
- F1206
- F1270
- F1271
- F1307
- F1345
- F1379
- F1441
- F1496
- F1531
- F1532
- F1565
- F1597
- F1598
- F1727
- F1762
- F1798
- F1800
- F1836
- F1898
- F1900
- F1960
- F2093
- F2160
- F2195
- F2224
- F2253
- F2297
- F2334
- F2367
- F2396
- F2433
- F2526
- F2560
- F2599
- F2657
- F2719
- F2786
- F2816
- F2849
- F2883
- F2884
- F2916
- F2948
- F3021
- F3048
- F3080
- F3118
- F3152
- F3186
- F3234
- F3266
- F3267
- F3331
- F3367
- F3368
- F3436
- F3467
