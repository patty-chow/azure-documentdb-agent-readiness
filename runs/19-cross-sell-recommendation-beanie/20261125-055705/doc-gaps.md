# Documentation and tooling gaps: 19-cross-sell-recommendation-beanie

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Index creation example and idempotent script

- **What was missing:** No idempotent script or concrete JSON file in the repo that calls DocumentDB's `createSearchIndexes`/`cosmosSearch` to create a vector index (dimensions, engine, and tuning parameters were not programmatically created). README points to manual steps but does not ship the index JSON.
- **Where the agent looked:** Repository files (README.md, seed.py), installed skills (documentdb-vector-search, documentdb-indexing) and Microsoft Learn vector-search docs via learn_microsoft_docs_search.
- **Effect on this build:** Builder did not create the cluster index automatically; vector retrieval was implemented in-app rather than via $search because the sample didn't apply a vector index.
- **Suggested fix (mcp_tool_or_description):** Provide an `index_example.json` and a small `create_index.py` script that reads EMBEDDING_DIMENSIONS and emits the `createSearchIndexes` payload for vector-diskann/vector-hnsw/vector-ivf with recommended parameter sets for small/medium/large datasets, plus a README subsection: 'How to apply the index via DocumentDB MCP or portal and how to verify readiness.'

## [high] Idempotent seed and bulk-upsert example

- **What was missing:** No example of using bulkWrite/upsert in seed script to ensure idempotency; current script creates random order ids leading to duplicate orders on repeated runs.
- **Where the agent looked:** seed.py, documentdb-bulk-write guidance in skills and Microsoft Learn bulk write docs.
- **Effect on this build:** Re-running seed.py will create new order documents and change pair counts; the claimed 'idempotent' behavior in comments is not enforced by code.
- **Suggested fix (agent_kit_rule):** Add a seed pattern in the agent kit showing deterministic ids or upsert-based bulkWrite for orders and product_pairs, with a code snippet demonstrating UpdateOne(..., upsert=True) in batches and a resume checkpoint file.

## [medium] Index tuning and scale guidance discoverability

- **What was missing:** The README recommends DiskANN but does not include concrete tuning knobs (lBuild/lSearch/ef, maxDegree, nlist) or example parameter values for the sample's seed size.
- **Where the agent looked:** README and repo, documentdb-vector-search skill and Microsoft Learn vector-search doc.
- **Effect on this build:** Builders and users lack ready defaults to apply to a cluster; they might choose suboptimal index parameters for their scale.
- **Suggested fix (discoverability):** Add a 'Vector index tuning' subsection to README with three presets (demo/small/production) listing engine choice and explicit params and a one-line explanation when to pick each.

## [medium] Guidance for request-time embeddings vs stored-product-embedding basket

- **What was missing:** No explicit documentation guidance that explains tradeoffs between embedding the basket at request time with OpenAI vs computing a basket embedding from stored product embeddings (and which is preferred for this sample).
- **Where the agent looked:** README, seed.py, documentdb-vector-search and documentdb-data-modeling skills.
- **Effect on this build:** Builder chose stored-product averaging; sample diverged from the prompt expectation to call OpenAI at request time and to run server-side $search. Users may be confused which approach to use.
- **Suggested fix (learn_doc):** Add a README section 'Basket embedding: Options and tradeoffs' explaining (a) request-time embeddings (pros/cons, additional latency, required OpenAI key), (b) precomputed product embeddings averaged at query time, and an explicit note about how to adapt the code to use $search with a request-time OpenAI vector.

## [low] Instruction to treat DOCUMENTDB_URI as opaque SRV URI

- **What was missing:** README and .env.example show a sample mongodb+srv URI but the repo does not instruct authors to avoid hardcoding host/port parsing (some docs and older examples assume port 10255).
- **Where the agent looked:** README, .env.example, documentdb-azure-deployment and MCP docs.
- **Effect on this build:** Code correctly passes DOCUMENTDB_URI through to the driver, but a future builder might parse host/port and break SRV URIs.
- **Suggested fix (discoverability):** Add a one-line rule in README: 'Pass DOCUMENTDB_URI unchanged to the driver (do not parse host/port); vCore clusters typically publish mongodb+srv URIs.'

## [low] Make explicit that OpenAI key is optional for verification

- **What was missing:** README notes placeholder embeddings, but there is no detailed note for CI/verification about how to run end-to-end with real embeddings.
- **Where the agent looked:** README and seed.py.
- **Effect on this build:** The seed ran with placeholders; end-to-end semantic ranking was not validated without OPENAI_API_KEY.
- **Suggested fix (discoverability):** Add a README paragraph describing how to set OPENAI_API_KEY for production/semi-production verification and the expected impact, plus a small test command to verify embeddings were created by OpenAI.

