# Documentation and tooling gaps: 10-support-ticket-rag-assistant

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Public guidance for pseudo-embeddings in tests

- **What was missing:** No Microsoft/Azure public doc explicitly states that deterministic pseudo-embeddings should be used only for unit tests/CI and not in integration/production. The earlier agent search found no guidance (P15 flagged prior_knowledge_only).
- **Where the agent looked:** Installed agent skills (documentdb-vector-search), Microsoft Learn searches for pseudo-embedding guidance (see run logs).
- **Effect on this build:** The builder used deterministic pseudo-embeddings for offline verification and tests; this is sensible, but an agent may use them inappropriately for production unless guidance is explicit.
- **Suggested fix (learn_doc):** Title: "Testing embeddings with Azure DocumentDB"
Outline: short guidance that deterministic pseudo-embeddings are useful for unit tests/CI only; examples of a pseudo-embedder; a table showing what metadata (model_name, dims, version) to store for production vectors; recommended migration/reindex steps when switching to real embeddings.

## [high] LlamaIndex → DocumentDB adapter & compatibility guidance

- **What was missing:** No documented, discoverable LlamaIndex adapter pattern to map LlamaIndex document objects to DocumentDB documents with an `embedding` number[] field and cosmosSearch index creation steps. The readiness report noted this gap.
- **Where the agent looked:** Installed skills (no LlamaIndex adapter), Microsoft Learn vector-search pages, agent-kit skills.
- **Effect on this build:** The builder removed llama-index due to dependency conflicts and implemented direct OpenAI calls. A documented adapter would let agents follow the starter prompt exactly and avoid ad-hoc implementations.
- **Suggested fix (agent_kit_rule):** Short agent-kit recipe: file layout and minimal adapter code showing how to: (1) convert LlamaIndex nodes to Mongo docs with `embedding` and metadata, (2) create a compatible cosmosSearch vector index (example createIndexes payload), (3) retrieve and map searchScore back to LlamaIndex result objects. Include pinned versions that are known to interoperate with Python 3.13 or recommend a runtime (e.g., Python 3.11) tested with llama-index releases.

## [high] Unit-testing without live cluster (mocks/examples)

- **What was missing:** No example tests that mock DocumentDB interactions (e.g., using mongomock or by injecting a fake get_client) so the unit tests currently need a live cluster.
- **Where the agent looked:** Repository tests and installed skills.
- **Effect on this build:** Gallery samples are expected to include tests that run offline; current tests require a live cluster so CI or a contributor without a cluster cannot run them rapidly.
- **Suggested fix (sample_or_quickstart):** Add a tests/mock_test.py that demonstrates replacing src.db.get_client with a mongomock client or monkeypatching the search functions; show how to run unit tests without DOCUMENTDB_URI. Include a short paragraph in README on test strategies (mock vs integration).

## [high] Naming disambiguation: Azure DocumentDB vs Cosmos DB (vCore vs RU)

- **What was missing:** The product/name distinctions that commonly confuse agents (DocumentDB vCore vs Cosmos DB RU) should be surfaced clearly on the quickstart and agent-kit skills.
- **Where the agent looked:** readiness findings and skill docs.
- **Effect on this build:** Some CLI/ARM examples and the .env.example host pattern could be copied incorrectly if the user expects legacy cosmos connection patterns. This build avoided provisioning but incorrect naming could mislead future maintainers.
- **Suggested fix (naming_or_disambiguation):** A short 'Which product to use' banner in the quickstart describing differences (mongoClusters vs databaseAccounts, host suffix patterns, ports), with two copy-paste .env.example variants for the two endpoint types and the correct CLI/Bicep command groups to use.

## [medium] Index tuning guidance discoverability in README

- **What was missing:** The README explains how to run the sample but does not explain how to change vector index type/parameters for a larger corpus or production (m, efConstruction, maxDegree, lBuild/lSearch settings).
- **Where the agent looked:** Project README and installed skills. Microsoft Learn has index tuning guidance, but the sample's README does not link to it.
- **Effect on this build:** Builders may ship the sample with HNSW defaults that are not appropriate for larger datasets; users will have to rediscover tuning guidance externally.
- **Suggested fix (discoverability):** Add an "Index tuning" subsection to README summarizing when to use HNSW vs DiskANN vs IVF, the key parameters to tune (with example ranges), and a link to the DocumentDB vector-search Learn page. Include a small example of switching to DiskANN for production and the cost/compute implications.

## [medium] Model-default decisions document

- **What was missing:** Some build choices used 'model_default' as the reason (e.g., choosing gpt-4o-mini). The sample and agent-kit lack a documented list of recommended default embedding/chat models and when to override them.
- **Where the agent looked:** decisions.jsonl and README.
- **Effect on this build:** Using model defaults without documented rationale can lead to inconsistent choices by different builders and hidden drift when models are updated.
- **Suggested fix (agent_kit_rule):** A short agent-kit RULE listing recommended default models (embedding + chat) for samples, along with a one-line justification and the expected embedding dim for each model. E.g., 'text-embedding-3-small (1536) — use for small/medium demos; text-embedding-3-large (3072) for higher recall'.

