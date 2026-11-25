# Documentation and tooling gaps: 09-crypto-wallet-activity-analyzer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LangChain agent examples and wiring

- **What was missing:** The developer prompt asked for a LangChain agent, but public docs and the installed skills did not provide a minimal, copy-paste LangChain 'Tool' + 'initialize_agent' example that integrates a DocumentDB aggregation function.
- **Where the agent looked:** Installed skills (documentdb-natural-language-querying and documentdb-driver), Microsoft Learn quickstarts, and LangChain docs checked by the builder.
- **Effect on this build:** Builder implemented the core analysis and a local/optional-OpenAI summarizer but did not wire a LangChain Agent. This left the sample functionally correct but not matching the starter prompt's 'LangChain agent' deliverable.
- **Suggested fix (agent_kit_rule):** Provide a short agent-kit snippet under DocumentDB samples: 'LangChain agent + PyMongo Tool' showing how to create a langchain Tool wrapping a function like run_aggregation_and_index and how to call initialize_agent(tools, llm, agent='zero-shot-react-description'). Include a tiny example file 'agent_wrapper.py' that samples can adopt.

## [high] Retry/backoff recipe for aggregations and writes

- **What was missing:** The public docs describe reliability principles, but a concrete small recipe for wrapping PyMongo aggregation and write calls with retries/backoff+jitter (and example code) is not present as a one-paragraph sample.
- **Where the agent looked:** Reliability docs, quickstarts and driver best-practices in installed skills.
- **Effect on this build:** No retry/backoff implementation was added to the sample; network/transient faults could cause sample runs to fail on less-reliable networks.
- **Suggested fix (learn_doc):** A short 'Retry patterns for PyMongo' page with sample code using tenacity or a simple retry loop showing exponential backoff and jitter for aggregates and writes, along with guidance to keep writes idempotent.

## [high] Tests-without-live-cluster guidance

- **What was missing:** The team expects samples to include unit tests that run without a live cluster, but Microsoft docs do not have a short, discoverable how-to for mocking DocumentDB access in Python samples (e.g., using mongomock or monkeypatching get_db).
- **Where the agent looked:** Quickstarts, install docs, repository samples and installed skills.
- **Effect on this build:** No tests were added; builders must create test harnesses themselves or follow a standardized example.
- **Suggested fix (sample_or_quickstart):** Add a 'Testing DocumentDB samples' page showing two approaches: (1) use mongomock to emulate collection APIs for unit tests; (2) run tests against the local DocumentDB gateway Docker image (port 10260) with instructions and a Docker Compose example; include a sample pytest file.

## [high] Prior-knowledge contradictions (billing / RU model)

- **What was missing:** A clear, prominent note that Azure DocumentDB vCore MongoDB clusters are billed by compute tier (vCores / M-tier) and storage, and not by RUs, to prevent confusion with Cosmos RU-based offerings.
- **Where the agent looked:** Product overview and pricing pages; readiness findings show agents are likely to confuse the models.
- **Effect on this build:** No direct effect on this sample, but mistaken assumptions about RU-based controls would mislead builders attempting to provision or scale clusters.
- **Suggested fix (discoverability):** Add a short 'Billing and scaling' blurb in the quickstart clearly contrasting vCore/compute-tier vs RU-based Cosmos accounts, with pointers to the pricing page and example CLI/Bicep flags.

## [medium] Driver pinning guidance

- **What was missing:** The checklist expects samples to pin driver versions exactly. Microsoft Learn/docs do not provide a single canonical 'pin these exact driver versions' statement for PyMongo and LangChain integration; guidance shows tested versions in examples but not a pinned default for samples.
- **Where the agent looked:** Microsoft Learn quickstarts and compatibility pages (Quickstart: Use Azure DocumentDB with MongoDB driver for Python, Django quickstart), repo readme and requirements.txt.
- **Effect on this build:** The builder elected to use ranged version constraints (pymongo>=4.3,<5.0) instead of exact pins. This leaves reproducibility and exact compatibility ambiguous and was flagged in decisions (D003) as 'pinned' although code shows ranges.
- **Suggested fix (discoverability):** Add a short 'Supported client versions' subsection on the DocumentDB Python quickstart that lists a tested-and-recommended set of exact driver versions for samples (e.g., PyMongo 4.20.1) and a suggested constraints file content. Example content: title 'Supported driver versions' and a short table mapping Python versions to tested PyMongo versions and pinned requirement lines to copy.

## [medium] Server-side z-score example

- **What was missing:** There is no Azure-DocumentDB-specific example that shows how to perform z-score outlier detection entirely server-side using aggregation operators (the two-pass compute mean/stdDev then join pattern).
- **Where the agent looked:** Microsoft Learn aggregation docs and operator pages; search for '$stdDevSamp' and aggregation patterns.
- **Effect on this build:** The builder computed outliers client-side; an explicit server-side example would let agents implement outlier detection inside aggregation_tool (meeting the starter prompt's wording exactly).
- **Suggested fix (sample_or_quickstart):** Add a short 'Analytics Patterns' page that includes a 'z-score outlier detection' aggregation example: a pipeline that computes mean/stdDev via $group or $setWindowFields and then $lookup/$set to compute z-scores per-day, with note on allowDiskUse and memory considerations.

## [medium] IaC mapping: which resource to use for vCore MongoDB clusters

- **What was missing:** Agents and builders often confuse older 'databaseAccounts' resource types with the vCore 'mongoClusters' resource type. The docs provide this information but cross-links and a short explicit decision table are not as discoverable as they should be.
- **Where the agent looked:** Cloud quickstarts and IaC reference pages; readiness notes flagged this confusion (readiness_findings Q01-Q03).
- **Effect on this build:** Builder chose not to provision resources (per run policy). However, if an agent had attempted to add IaC it could have used the wrong resource type.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Which resource to use' table on the top-level quickstart that maps product scenarios to the exact ARM/Bicep/Terraform resource types (vCore MongoDB -> Microsoft.DocumentDB/mongoClusters; RU-based Cosmos -> Microsoft.DocumentDB/databaseAccounts) and provide a minimal AzAPI/Terraform snippet for a small test cluster.

