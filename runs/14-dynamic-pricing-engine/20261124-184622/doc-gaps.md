# Documentation and tooling gaps: 14-dynamic-pricing-engine

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Agent-LangChain tool-wrapper examples

- **What was missing:** No copy-paste, authoritative example showing how to expose DocumentDB MCP server operations as LangChain Tool classes and how to wire initialize_agent safely across LangChain versions.
- **Where the agent looked:** Installed skills (documentdb-*), Microsoft Learn, open-source samples; readiness findings show a missing worked example.
- **Effect on this build:** The builder tried to use LangChain initialize_agent, hit import errors and switched to a robust lightweight orchestration (D012/D024). If a canonical wrapper existed, the fragile initialize_agent approach could have been used or at least ported more easily.
- **Suggested fix (agent_kit_rule):** Add a 'LangChain tool wrappers for DocumentDB' page in the agent-kit: show a small Tool class or function wrapper pattern for pymongo-based queries, include conditional examples for both older and newer LangChain import paths (ChatOpenAI vs langchain.chat_models), and a tiny test harness that uses a mock LLM so authors can validate tool wiring without an API key.

## [high] Not sending secrets to LLMs (DocumentDB-specific guidance)

- **What was missing:** No Azure DocumentDB public guidance explicitly addressing LLM/agent patterns that might mistakenly send connection strings or keys to the model; the practice exists in prior knowledge but not in company docs.
- **Where the agent looked:** Microsoft Learn, installed skills, and open web searches for 'Azure DocumentDB do not send connection string to LLM' returned no useful official guidance.
- **Effect on this build:** The builder implemented tools correctly and did not send secrets to the model, but agents and builders could accidentally leak secrets when wiring tools to LLM prompts unless guidance is explicit.
- **Suggested fix (learn_doc):** A short 'LLMs and secrets' note on the DocumentDB security quickstart: single paragraph stating 'Do not provide connection strings or DB keys to LLM prompts; instead expose parameterized tools that call the DB on the model's behalf' and a small example showing correct vs incorrect patterns.

## [high] Pinning tested driver versions

- **What was missing:** Guidance that sample authors should pin driver versions to the ones that the quickstarts/tests were built against (and an example pinned requirements.txt).
- **Where the agent looked:** Microsoft Learn quickstarts/doc pages include 'tested driver version' notes in some quickstarts but there is no centralized 'pin your dependencies' sample guidance.
- **Effect on this build:** The builder left flexible dependency specifiers (>=) that resulted in LangChain version mismatches causing import errors and a change in agent implementation.
- **Suggested fix (discoverability):** Add a small 'Pin runtime & dependency versions' section to the DocumentDB sample guidance that shows an example requirements.txt with pinned versions used in CI and explains how to re-run with the requirements-dev.txt file used for the gallery build. Also add a CI snippet that validates 'pip install -r requirements.txt' and a smoke run of the CLI in CI.

## [high] Retry / backoff guidance in sample patterns

- **What was missing:** A short copy-paste implementation (or recommended small helper) showing how to add exponential backoff retries around pymongo operations in Python samples.
- **Where the agent looked:** Readiness notes and installed skills mention retries but there is no small snippet in the agent-kit demonstrating recommended retry wrappers and idempotency patterns for writes.
- **Effect on this build:** The sample omitted retries/backoff, leaving production resilience untested and increasing the chance of transient failures being exposed to users.
- **Suggested fix (sample_or_quickstart):** Provide a 1-file helper (db_retry.py) demonstrating a minimal tenacity-based retry decorator for reads/writes, and show a small code snippet in README that instructs authors to use it for any networked DB call. Explain which operations should be idempotent and how to detect unknown outcomes.

## [medium] LLM provider and env var guidance

- **What was missing:** No official, canonical guidance on which LLM/embedding provider to prefer for DocumentDB samples or which env var names to standardize (OPENAI_API_KEY and MODEL are used by the sample, but this is a builder choice).
- **Where the agent looked:** Microsoft Learn quickstarts, sample run readiness notes, installed skills; searches for 'LangChain provider recommendation for DocumentDB' yielded no canonical guidance.
- **Effect on this build:** The builder made model-default choices (D004, D009, D020). That left the sample reliant on OpenAI by convention and required a developer decision that should be documented centrally.
- **Suggested fix (discoverability):** Add a short 'LLM provider and environment variables' doc page in the agent-kit describing recommended env var names (OPENAI_API_KEY, MODEL), how to switch to Azure OpenAI, and a note on test-mode fallbacks (mock LLM). Include example snippets for OpenAI and Azure OpenAI and a sentence recommending not to commit keys.

## [medium] Index-creation best practice for seed scripts

- **What was missing:** Advice for samples: create indexes after bulk seeding or use nonblocking createIndex for large historic datasets and include a note in seed scripts.
- **Where the agent looked:** Indexing docs on Learn (found) but no sample-level rule telling sample authors where to put init_indexes in the seed flow.
- **Effect on this build:** The sample creates indexes during seed startup. For a small sample this is fine; for larger seeded datasets authors might want to create indexes afterwards to reduce write cost and blocking.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a 1-paragraph cookbook: 'For seeds < 10k records create indexes before or during seeding; for larger seeds run seed -> create indexes (nonblocking) -> verify createIndex progress with db.currentOp()'. Provide an example change to seed.py showing idempotent post-seed createIndex.

