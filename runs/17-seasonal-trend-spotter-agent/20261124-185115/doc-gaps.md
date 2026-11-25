# Documentation and tooling gaps: 17-seasonal-trend-spotter-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Unit tests that run without a live cluster

- **What was missing:** A test harness with unit tests that mock the MongoDB driver and web-search provider so tests run without a live DocumentDB cluster or external API keys.
- **Where the agent looked:** Repository (no tests present) and agent-kit skills (no canonical test harness template found).
- **Effect on this build:** No automated unit tests exist; maintainers must run manual steps or use live resources for verification, which increases reviewer burden and reduces CI friendliness.
- **Suggested fix (agent_kit_rule):** Provide a sample pytest test suite in the agent kit demonstrating how to mock pymongo.MongoClient (or use mongomock) and how to monkeypatch web-search calls, including an example CI configuration that runs tests with TEST_WITH_LIVE=false.

## [high] Seed/ingest batching guidance

- **What was missing:** DocumentDB-specific guidance on recommended batch sizes and backoff strategy for bulk seeding in the agent-kit; public skills did not include a concrete default batch size to use for bulkWrite.
- **Where the agent looked:** searches for 'DocumentDB bulkWrite batch size guidance' and the installed skills; found only general prior knowledge but no DocumentDB-specific batch-size rule.
- **Effect on this build:** The seed script uses a per-document upsert loop; it worked for small data during verification but lacks scalable bulkWrite examples and backoff logic that a builder would use for larger datasets.
- **Suggested fix (learn_doc):** A short 'Seeding at-scale' page in the agent kit: show an idempotent bulkWrite example with an env-driven BATCH_SIZE default (e.g., 500), example exponential backoff on transient errors, and how to observe cluster throttling metrics.

## [high] Clear /search API contract (empty query and embedding failures)

- **What was missing:** A canonical example endpoint (e.g., FastAPI snippet) and error payload shape documenting how /search should respond to empty queries and to embedding/search failures.
- **Where the agent looked:** No sample HTTP endpoint in repository; agent-kit skills do not include a canonical /search contract for LangChain-style agents combining DB+web signals.
- **Effect on this build:** No endpoint exists; callers cannot rely on a uniform error contract. This increases integration friction for downstream apps that expect a 400 for empty queries or a structured error if embeddings fail.
- **Suggested fix (agent_kit_rule):** Provide a short 'HTTP contract' snippet in the sample README: example FastAPI /search handler that returns 400 on empty q, 502/503 on external-api failure with structured JSON {error:..., code:...}, and an example of the mock fallback path.

## [medium] Driver version recommendation and tested versions

- **What was missing:** A clear, discoverable statement in the agent-kit / quickstart that lists the tested pymongo (and related) driver versions for Python and an explicit recommendation to pin to those exact versions.
- **Where the agent looked:** Agent loaded documentdb-driver skill and ran learn_microsoft_docs_search; relevant Quickstarts mention tested PyMongo versions (e.g., PyMongo 4.19.0) but the recommendation is not surfaced in the agent-kit README.
- **Effect on this build:** Builder chose version ranges (pymongo>=4.4,<5). This leaves potential for non-reproducible installs or subtle incompatibilities if a newer patch introduces changes. The build passed but the exact tested version wasn't recorded.
- **Suggested fix (discoverability):** Add a short 'Tested dependencies' section to the sample README and to the documentdb-driver skill that lists pinned versions (example: pymongo==4.19.0, langchain==1.5.2, openai==3.59.0) and provide a constraints.txt for reproducible installs. Include a short sentence linking to Microsoft quickstarts that document tested driver versions.

## [medium] Web-search timeouts & fallback rule for agents

- **What was missing:** A concise agent-kit rule saying external search calls should use a bounded timeout, retries, and deterministic fallback (mock) so the agent remains responsive when external APIs are slow or unavailable.
- **Where the agent looked:** Installed skills and web searches returned no DocumentDB-specific guidance for external API timeouts (this is application-level best practice).
- **Effect on this build:** The sample does include a timeout (requests.get timeout=10) and a mock fallback, but this application-level decision is only present in code and not surfaced as a recommended rule in the agent-kit docs, so other builders may omit it.
- **Suggested fix (agent_kit_rule):** Add a one-paragraph rule to the agent-kit recommending default timeouts (e.g., 5–10s), a max retry count, and mandatory deterministic fallback for external web-search tools. Include small code snippets for requests-based and async clients.

## [medium] UTC temporal-field guidance for seasonal comparisons

- **What was missing:** A short, public sentence in the agent-kit stating 'store temporal fields as BSON Date in UTC' and an example that shows how to compute seasonal ranges with UTC dates.
- **Where the agent looked:** Search for Azure DocumentDB date/time guidance returned no authoritative DocumentDB-specific page; it remains prior knowledge across MongoDB-like systems.
- **Effect on this build:** The sample uses datetime.utcnow(), which is correct in practice, but an explicit doc would help other builders avoid timezone bugs when authors rely on local time.
- **Suggested fix (learn_doc):** An example snippet in the data-modeling or aggregation quickstart demonstrating 'sale_date: datetime.utcnow()' and showing how to derive seasons with $month and explicit UTC ranges; add a short note on indexing date fields.

