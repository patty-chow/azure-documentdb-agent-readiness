# Documentation and tooling gaps: 13-chronic-disease-risk-predictor

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] WriteConcern / readPreference guidance

- **What was missing:** Authoritative, service-specific guidance on recommended writeConcern and readPreference settings for DocumentDB workloads (PHI/critical writes vs low-latency reads). The discovery step found no Learn/MS doc that directly maps these MongoDB primitives to Azure DocumentDB best-practices; the checklist expects this to be explicit.
- **Where the agent looked:** learn.microsoft.com DocumentDB pages and installed skills (documentdb-connection, documentdb-security); searches: "Azure DocumentDB writeConcern", "Azure DocumentDB readPreference".
- **Effect on this build:** The sample used default client options. Without explicit guidance, builders may pick inappropriate settings (e.g., wrong durability/latency trade-offs) for PHI writes.
- **Suggested fix (learn_doc):** A short guidance page: 'DocumentDB: readPreference and writeConcern recommendations' including (1) recommended writeConcern for PHI/critical writes (e.g., majority or equivalent pattern in DocumentDB), (2) recommended readPreference for low-latency scenarios, (3) examples showing how to set them in a pymongo MongoClient URI and via options, and (4) references to trade-offs. Include a snippet of code and a brief decision table.

## [high] MCP management-tools opt-in documentation

- **What was missing:** Clear documentation for the documentdb MCP tools about the management-tools opt-in flag (ENABLE_MANAGEMENT_TOOLS) and the operational constraints when management tools are disabled by default in some environments.
- **Where the agent looked:** events.jsonl tool errors and the documentdb MCP skill resources. I searched the MCP documentation in the installed skills and Learn docs for how to enable management tools but the run encountered a ToolExecutionException mentioning ENABLE_MANAGEMENT_TOOLS.
- **Effect on this build:** The documentdb_create_index MCP helper failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.' which blocked the recommended MCP-assisted index creation path and forced driver-level attempts and fallbacks.
- **Suggested fix (mcp_tool_or_description):** In the MCP README and the documentdb-mcp-setup skill: (1) document the ENABLE_MANAGEMENT_TOOLS opt-in and how to set it in MCP profiles, (2) show a safe 'create-index' flow that logs both the attempted payload and the server error details if create fails, and (3) provide guidance for environments where MCP management is intentionally disabled.

## [high] Seed-index ordering and pre-existing incompatible documents

- **What was missing:** A small operational note and a safe-by-default pattern: either create the vector index before ingest, or detect and refuse to create an index if existing documents have wrong-dimension embeddings, and suggest creating a fresh collection.
- **Where the agent looked:** seed.py and retriever.ensure_vector_index() behavior; events show db.command returned 'expected 1536 dimensions, not 3'.
- **Effect on this build:** Index creation failed because incompatible documents were present in the collection; the build then used a client-side fallback. This made the intended server-side vector search unverified in this run.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and seed-script change: ensure_vector_index() should check for existing documents with embedding fields and verify their length matches EMBEDDING_DIMS before attempting index creation; if mismatched, fail with an explicit message and offer (a) a 'create-in-new-collection' option, or (b) delete/repair guidance. Add a sample flag SEED_CREATE_INDEX_FIRST to the seed script to create index before seeding.

## [high] WriteConcern/readPreference discovery

- **What was missing:** Explicit, discoverable guidance that maps MongoDB writeConcern/readPreference options to Azure DocumentDB semantics for common workloads.
- **Where the agent looked:** learn.microsoft.com and installed skills; search terms: 'Azure DocumentDB writeConcern', 'readPreference' returned no authoritative mapping (see discovered_practices search results).
- **Effect on this build:** The sample used default client settings. For production PHI workloads, lack of authoritative guidance increases risk of incorrect choices.
- **Suggested fix (learn_doc):** Add a small 'Driver durability & read preferences' page showing recommended settings for PHI writes (durable/majority) and low-latency reads, with code examples for pymongo connection options and per-operation preference overrides.

## [medium] Deterministic offline embedding tests

- **What was missing:** A short, discoverable example showing how to run deterministic offline embedding generation for unit tests (pattern used here: seeded RNG + fallback) and how to mock or stub the embedding API reliably.
- **Where the agent looked:** learn.microsoft.com, agent skills and repo tests; searches for 'deterministic offline embedding tests' returned no authoritative guidance for DocumentDB.
- **Effect on this build:** The sample implemented a seeded fallback and tests used mongomock, but other builders could write brittle tests that call live embedding/LLM services or inject non-deterministic vectors into indexes.
- **Suggested fix (sample_or_quickstart):** A short sample/test guide titled 'Testing DocumentDB vector apps offline' giving patterns: deterministic seeded embedding fallback, using mongomock for DB calls, example pytest fixtures, and how to assert retrieval logic independently of embedding model outputs.

## [medium] Index parameter tuning guidance in sample README

- **What was missing:** The sample README notes the chosen index kind and dims but lacks practical tuning guidance (when to change maxDegree/lBuild/lSearch or switch algorithm) and concrete instructions for larger datasets.
- **Where the agent looked:** app/README.md and installed vector-search skill docs.
- **Effect on this build:** Builders have the code values in src/retriever.py, but README omission makes it harder for a sample user to understand trade-offs and where to change parameters safely.
- **Suggested fix (sample_or_quickstart):** A README subsection 'Index tuning and scaling' that explains the sample defaults, how recall/latency tradeoffs map to maxDegree/lBuild/efSearch/lSearch/numLists, and an example of how to measure and modify those settings with representative explain() and monitoring steps.

## [medium] LlamaIndex → DocumentDB retriever example

- **What was missing:** A concrete, copy-paste example showing how to adapt a DocumentDB $search retriever into a LlamaIndex Retriever (get_relevant_documents), including how to register it in ServiceContext and use it as agent memory.
- **Where the agent looked:** Installed skills and LlamaIndex docs; no pre-existing skill page that shows a direct LlamaIndex → DocumentDB retriever mapping was found by the discovery agent.
- **Effect on this build:** The builder implemented a functional workaround (passing retrieved_profiles into generate_narrative) rather than a LlamaIndex-backed memory component; this complexity discouraged a canonical LlamaIndex binding.
- **Suggested fix (sample_or_quickstart):** A short code example file 'examples/llamaindex_documentdb_retriever.py' that implements a class DocumentDBRetriever(get_relevant_documents) calling the retriever.retrieve_similar API and converting results to Document objects, plus a README snippet on how to plug it into ServiceContext/LLMPredictor.

