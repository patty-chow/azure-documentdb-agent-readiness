# Documentation and tooling gaps: 07-voice-of-customer-sentiment-hub

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & dimension guidance

- **What was missing:** Authoritative guidance pairing common embedding models (OpenAI/Azure/other) with their output dimensions and recommended ENV names (EMBEDDING_MODEL -> EMBEDDING_DIM) so samples can set correct defaults.
- **Where the agent looked:** Skills and Microsoft Learn; readiness findings recorded this gap (no single authoritative mapping page found).
- **Effect on this build:** Builder picked a reasonable default (text-embedding-3-small / 1536) but the choice is a model_default and must be documented for users to avoid silent dimension mismatches when they change providers.
- **Suggested fix (learn_doc):** A short Microsoft Learn page or sample README section titled 'Embedding model names and dimensions' listing common models (text-embedding-3-small:1536, text-embedding-3-large:1536, all-MiniLM-L6-v2:384, etc.), the env var names (EMBEDDING_MODEL, EMBEDDING_DIM), and a runtime validation snippet to assert the embedder returns the expected length.

## [high] Index parameter defaults for small samples

- **What was missing:** Concrete default ANN tuning parameters (HNSW M / efConstruction, DiskANN lBuild / lSearch) for small sample datasets and instructions on when/how to increase them for production.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search docs; the skill gives theory but no sample-size defaults.
- **Effect on this build:** create_search_indexes in the sample used vector-hnsw but omitted explicit tuning; users won't know safe default values to start with and may misconfigure for larger scales.
- **Suggested fix (learn_doc):** Add a 'Vector index tuning for sample vs production' guide: recommended values for <10k docs (HNSW M=8-16, efConstruction=100), for 10k-100k (M=16-32, efConstruction=200), and for production (DiskANN) with examples of how to change createSearchIndexes payload and the tradeoffs.

## [high] createSearchIndexes availability and fallback recipe

- **What was missing:** A dedicated Microsoft Learn note that states which cluster types/tiers support createSearchIndexes and a canonical fallback recipe when the command returns CommandNotSupported (store embeddings + client-side NN or fallback text index).
- **Where the agent looked:** Search queries for createSearchIndexes availability returned no single authoritative page documenting all scenarios; discovery returned prior_knowledge_only for fallback guidance.
- **Effect on this build:** The builder handled the cluster returning CommandNotSupported, but an agent without this workaround would have failed to produce the demo outputs or would have stopped the build.
- **Suggested fix (learn_doc):** Page titled 'Search index availability and fallbacks' that: (a) lists createSearchIndexes supported SKUs/tiers, (b) gives copy-paste index-creation JSON and expected errors when unsupported, and (c) prescribes a fallback implementation (store embeddings + example client-side approximate-NN snippet) and sample code.

## [high] RU vs vCore provisioning clarity

- **What was missing:** A clear, prominent statement on the overview / quickstart pages explaining that Azure DocumentDB (vCore) uses M-tier (vCore) compute + storage billing and not Cosmos DB RU/s.
- **Where the agent looked:** Readiness findings and skills; this confusion surfaced repeatedly in the readiness report where cold answers used RU/s.
- **Effect on this build:** Builders might use the wrong provisioning model or IaC resource type leading to wrong CLI/Bicep usage and failed deployments.
- **Suggested fix (naming_or_disambiguation):** Add a 'How this product is billed' section to the Azure DocumentDB overview with a one-line comparison to Cosmos RU billing and explicit examples of the correct resource type (Microsoft.DocumentDB/mongoClusters) and CLI commands (az documentdb mongocluster).

## [medium] Beanie compatibility note (Motor vs AsyncPyMongo)

- **What was missing:** Clear guidance on driver/ODM compatibility: whether Beanie remains the recommended ODM and whether Motor vs AsyncPyMongo is preferred for DocumentDB, and examples for both stacks.
- **Where the agent looked:** documentdb-driver skill and Beanie docs; no authoritative statement reconciles the two.
- **Effect on this build:** Builder attempted Beanie+Motor, encountered pydantic-core build issues and introduced a pymongo fallback; a clearer note would let agents choose a path that is broadly reproducible in typical developer runtimes.
- **Suggested fix (discoverability):** A short page 'Python ODM recommendations for Azure DocumentDB' showing 1) Beanie+Motor example and its pinned versions, 2) AsyncPyMongo+ODM alternative, and 3) a note on pydantic-core build constraints with recommended Python versions.

## [medium] Per-document LLM/embedder metadata guidance

- **What was missing:** Guidance recommending adding llm_model, embedding_model and embedding_dim metadata to documents when storing LLM/extraction results, and instructions to re-index when models change.
- **Where the agent looked:** Skills and Microsoft Learn returned no dedicated page for this LLM-integrated sample pattern (searches listed in discovered_practices).
- **Effect on this build:** The sample stores embeddings and extracted fields but does not persist model metadata per document; this makes safe reprocessing or detecting model/embedding-dimension drift harder.
- **Suggested fix (learn_doc):** Short 'LLM + embedder metadata' guidance with example Beanie/Mongo fields, code to write metadata at enrichment time, and a re-index checklist for when you change embedding dimensions or model.

## [medium] Tests without live cluster

- **What was missing:** A small test scaffold and examples demonstrating how to run unit tests without a live cluster using mocking/stubs for Motor/pymongo and LangChain.
- **Where the agent looked:** Repo and skills; the sample lacks offline tests and the skill docs don't include a test scaffold snippet for this exact scenario.
- **Effect on this build:** No unit tests were added; maintainers and reviewers cannot run automated checks locally without setting up a cluster or mocking strategy.
- **Suggested fix (agent_kit_rule):** Agent-kit rule and sample test code: provide pytest fixtures that monkeypatch the DB client and the langchain embedder/LLM; example tests for analyze_and_prepare, deterministic_embedding and enrich_and_store (mocked).

