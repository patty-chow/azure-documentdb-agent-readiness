# Phase 4 reviewer's notes

Written by the closing review agent of the triage workflow after reading the draft files.

## 1. Duplicates and near-duplicates to merge before filing

- **retryWrites=true and host-suffix fixes in the kit.** 13, 40, 81, 89, 90, 96, 102, 119 and 120 all patch the same three lines (connection/SKILL.md:60, driver-singleton-client.md:26, security-tls-required.md:26). 12, 14, 87 and 101 also fix `.documentdb.azure.com`. File one PR (013 or 040) and drop that fix from the others.
- **CLI group.** 004, 005, 007 and 040 (the `mongo-cluster` typo) overlap; 061 has the typo too. Merge into 004.
- **Entra/OIDC in the kit.** 014, 016, 017, 018, 041 and 101 overlap. Merge into one connection+security PR, with 018 (the enable/registration step) as one section of it.
- **Change streams in the kit.** 032, 033, 034, 035, 041, 093 and 105 each propose their own new file. Make it one skill.
- **Vector index templates in the kit.** 019, 021, 039, 086, 097, 113 and 114 overlap (plus 099 for HNSW). Merge into two PRs: storage plus templates, and app-side ensure_vector_index.
- **Retry and client factory in the kit.** 089, 090, 096 and 119 overlap; 096 is the superset.
- **Seeding and bulk load in the kit.** 053, 086 and 103 overlap.
- **Offline tests in the kit.** 052 and 091 overlap.
- **Env and scaffold conventions in the kit.** 012, 081 and 087 overlap.
- **Data modeling in the kit.** 071, 104 and 123 overlap (money and validators); 102 is close.
- **Gated tools in the MCP server.** 084, 108 and 112 overlap. Make one PR.
- **mongosh in the harness.** 062, 066 and 069 overlap.
- **Accelerator detection in the harness.** 058 and 070 are near-identical; 063 and 067 are related.
- **Design choices in the harness.** 042 and 054 overlap.
- **Prompt contract in the harness.** 050, 051, 083 and 109 overlap.
- **Empty builds in the harness.** 106 and 116 overlap.
- **Learn driver matrix.** 044, 075 and 126 are triplicates.
- **Learn vector search.** 043, 072 and 125 overlap.
- **Learn writes and transactions.** 076 and 124 overlap; 077 and 128 (bulk ingestion) overlap.
- **Learn Entra.** 046 and 074 overlap.
- **MCP-server routing in the kit.** 132 and 133 overlap.

## 2. Wrong or doubtful repository

- **006 and 073 (learn-docs).** The CLI reference pages are generated from Azure/azure-cli-extensions, and the ARM/AVM text has its own repos. Split those parts out.
- **074 and 075 are typed "pr" against learn-docs.** They should be learn-feedback unless someone will open a PR against the docs repo.
- **068 is tagged to the harness repo but is a kit note.** Harmless, since it is dropped.
- **118 (harness mcp.json) is really the root cause behind 108 and 112.** File it first, and frame the MCP issues as UX problems, not bugs.
- **Bucket "mcp-server" contains themes 113–121, which are mostly kit and harness items.** This is a clustering artifact. Check that no counts are attributed to documentdb-mcp.
- **132 and 133 state that the Azure MCP Server has no DocumentDB tools,** but no draft targets microsoft/mcp itself.

## 3. Missing themes

Every bucket has at least one theme, so coverage by bucket is complete. Gaps by topic:

- **documentdb-mcp README.** It presents localhost:27017 as the local URI. This is noted only as a follow-up in 031 and needs its own draft.
- **The Azure MCP Server (microsoft/mcp).** It has no draft for adding DocumentDB tools or a pointer to the dedicated server.
- **azure-cli-extensions help text.** There is no draft for the deprecation or cross-link note on `az cosmosdb mongocluster`.
- **Learn's own contradiction on retrywrites.** No Learn theme asks Learn to settle this; it appears only as a side note in 126.
- **Kit CI.** No draft proposes a kit lint step that blocks host suffixes and retryWrites values that disagree with the canonical string.

## 4. File first

1. **118** fixes the harness MCP flags; it removes about 88 false tool_unavailable results and re-baselines the experiment.
2. **040, merged with 013** is P0: the kit contradicts itself on retryWrites, the host suffix and the CLI spelling, and every build loads these files.
3. **004, merged with 005 and 007:** 85 of 100 samples fell back to `az cosmosdb`; the fix is small and clear.
4. **015:** the kit gives no billing model, so 92 of 92 cold answers assumed RU/s and 32 audit checks were falsely marked violated.
5. **039 together with 097:** the number[] rule and app-side index creation. Vector search silently failed in real builds.
6. **016, merged with 017 and 018:** Entra data-plane auth, misunderstood in 67 samples, with working code already on Learn.
7. **108, merged with 084 and 112:** makes the gated-tool refusal actionable and names a driver fallback. Real UX friction across 32 samples.
8. **058/070 plus 107:** stop the harness flagging the installed kit as missing and grading against RU-API practices. Without this, later runs keep producing noise.

## 5. What a PM should know before approving

- **Retry-writes contradiction.** 013 says Learn does not claim retryable writes are unsupported, and it softens the kit's rationale. 040, 074, 090 and 102 assert the opposite ("required; not supported; causes write errors"). Filing both stances would embarrass the team. Get the engineering answer first.
- **Artifacts that are not product gaps.** Many high counts come from the cold quiz (model priors) or from the harness: mongosh, Bicep and documentdb-local reported as "missed accelerators"; the kit flagged as not installed; MCP tools left off; empty builds; Python 3.13 install failures. About a third of the actionable drafts are harness fixes. Re-run after 118, 058, 106 and 117 before quoting sample counts externally.
- **Counts are unstable.** Many drafts were edited for miscounts (for example 006: 3 versus 42/101; 112: 38→36; 047 recounted). Inconsistent n's in public issues undermine credibility.
- **Fragmentation.** About 95 drafts are marked ready. Filed unmerged, they would flood the kit with 30+ overlapping PRs that touch the same lines. Consolidate to roughly 15 kit PRs, about 8 Learn items, 3 MCP items and about 10 harness items.
- **Claims that need SME confirmation before anything is public:**
  - Change-stream limits: the 400 MB log, the 35-day PITR window and the Rebalancer conflict.
  - The $jsonSchema enum unsupported claim in 104.
  - That 16500/429 "is not returned" by vCore (096, 119).
  - Driver version floors (017 flags unverified .NET and Java versions).
  - The HNSW and IVF limits.
- **Learn drafts carry "preview" labels** (full-text search, multishard change streams). Confirm current GA status.
- **Repo framing.** 050, 051 and 083 were re-homed from a non-existent repo. The harness repo is someone else's fork upstream (abinav2307), so coordinate before filing there.

Drafts are in /Users/julietai/claude/azure-documentdb-agent-readiness/findings/phase4/drafts.
