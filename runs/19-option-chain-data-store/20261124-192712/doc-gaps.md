# Documentation and tooling gaps: 19-option-chain-data-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Pagination guidance for full-chain endpoints

- **What was missing:** No public guidance specific to DocumentDB addressing when API endpoints should implement pagination for large logical 'chain' result sets and recommended patterns (limit/offset, keyset pagination using strike, or server-side cursors).
- **Where the agent looked:** learn.microsoft.com (DocumentDB pages), general searches: 'Azure DocumentDB pagination best practices API responses large result sets'
- **Effect on this build:** Discovery agent recorded this as prior_knowledge_only (P14). The sample returns full chain without pagination; a public note would have led the builder to implement paging by default.
- **Suggested fix (learn_doc):** A short guidance page 'API pagination patterns for DocumentDB-backed endpoints' describing: when to use limit+offset vs keyset pagination, examples using 'strike' as a range key for keyset pagination, an example FastAPI snippet returning next_token, and sample .explain() checks for cursor performance.

## [high] Tests run guidance and environment constraints

- **What was missing:** A concise note on the preferred Python versions and compatibility matrix for FastAPI/pydantic/pydantic-core and guidance on when tests should be run under a specific runtime (CI matrix).
- **Where the agent looked:** project requirements, PyPI, and builder logs; the run failed pytest due to Pydantic/FastAPI import error on Python 3.13
- **Effect on this build:** The builder's tests could not be executed in this runner environment (builder_report 'pytest: could not complete... Python 3.13 pydantic forward-ref error'). Without a clear note/CI matrix, agents may attempt to run tests in incompatible environments.
- **Suggested fix (discoverability):** Add a short 'Test environment' section to the docs and agent-kit: supported Python versions (3.10/3.11 recommended), minimal pinned package combos that work out-of-the-box, and CI job examples that run tests under supported versions.

## [medium] Idempotent upsert guidance

- **What was missing:** No clear public Microsoft doc explicitly describing composing a deterministic _id or an explicit recipe for making UpdateOne upserts idempotent (compose key from underlying+expiry+strike+optionType).
- **Where the agent looked:** learn.microsoft.com (DocumentDB pages), searches: 'Azure DocumentDB guidance "make upserts idempotent deterministic _id"'
- **Effect on this build:** Discovery agent labeled this as prior_knowledge_only (P12). The builder implemented idempotency via UpdateOne with a composed filter, but agents had no canonical public guidance to cite when deciding whether to use a deterministic _id vs UpdateOne upserts.
- **Suggested fix (learn_doc):** A short 'Idempotent ingestion' page under the DocumentDB developer guide that: (1) explains strategies to make ingestion idempotent (compose _id, use UpdateOne upsert with deterministic filter, unique compound indexes); (2) gives code snippets for pymongo showing both approaches; (3) notes tradeoffs (indexing, uniqueness constraints).

## [medium] Write concern mapping docs

- **What was missing:** No clear public mapping guidance for MongoDB writeConcern semantics to DocumentDB vCore clusters (which durability/consistency options map to what behavior in this product).
- **Where the agent looked:** learn.microsoft.com DocumentDB pages, searches: 'Azure DocumentDB guidance "choose write concern w majority"'
- **Effect on this build:** Discovery agent marked write-concern guidance as prior_knowledge_only (P16). The sample leaves writeConcern at driver defaults; a public page would help sample authors choose explicit durable/writeConcern settings safely.
- **Suggested fix (learn_doc):** A compatibility/operations page that lists which writeConcern values are supported, how they map to the cluster's durability semantics, examples configuring MongoClient writeConcern in Python, and warnings about throughput/cost tradeoffs.

## [low] Agent kit rule: prefer explicit API choice

- **What was missing:** Some build decisions (e.g., using FastAPI) were taken from model defaults rather than explicit guidance; agents lack a small agent-kit rule recommending a preferred minimal web framework for Python samples or requiring the builder to justify an alternative.
- **Where the agent looked:** agent kit skill docs and the sample repo; decisions.jsonl shows model_default choices
- **Effect on this build:** Decision D003 used 'model_default' as reason_source; this is acceptable but generates inspectability gaps. If an agent picks a different framework by default it will produce slightly different sample shape.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: 'Python sample web framework: prefer FastAPI for new samples unless the prompt explicitly requests another framework; document the choice in decisions.jsonl with reason_source enabling discoverability.'

