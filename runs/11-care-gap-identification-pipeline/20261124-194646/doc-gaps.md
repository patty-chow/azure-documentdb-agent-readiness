# Documentation and tooling gaps: 11-care-gap-identification-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] PHI & LLM guidance for Azure DocumentDB samples

- **What was missing:** A Microsoft-hosted statement and short guidance page for DocumentDB that tells sample authors whether it's acceptable to send identifiable patient data to third-party LLMs, and specific redaction/consent/contract-language to include in sample READMEs.
- **Where the agent looked:** Searched with queries: 'Azure DocumentDB do not send PHI to LLM guidance', 'DocumentDB PHI LLM HIPAA', and reviewed documentdb skills — no authoritative public guidance for PHI+LLM specific to DocumentDB was found.
- **Effect on this build:** The agent code will include entire patient records (including contact info) in LLM prompts when OPENAI_API_KEY is provided. Without explicit public guidance, the builder did not redact identifiers and the sample as distributed would encourage potentially non‑compliant behavior.
- **Suggested fix (learn_doc):** A short Microsoft Learn page: 'Handling PHI when calling external LLMs from DocumentDB samples' — include (1) a clear admonition not to send identifiers to third-party LLMs unless a HIPAA-compliant contract is in place; (2) sample code patterns for de‑identifying records; (3) an opt‑in environment variable pattern for advanced users; (4) examples of using managed/private models or running a local LLM gateway.

## [high] Pin tested dependency versions (agent kit guidance)

- **What was missing:** A short policy in the agent-kit telling builders to pin exact package versions in requirements.txt or supply a constraints file for reproducible sample builds.
- **Where the agent looked:** README and requirements.txt in the sample; no agent-kit policy found prompting pinned deps by default.
- **Effect on this build:** requirements.txt uses >= ranges leading to potential drift; reproducible verification is harder and package incompatibilities can break the sample in future runs.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Pin exact versions in sample requirements.txt. When adding tests, record the python/pip matrix used during verification. Provide a sample pinned requirements.txt template and a script that generates a deterministic lockfile.'

## [high] Unit test patterns & local test harness

- **What was missing:** A short example/tests template in the agent-kit demonstrating how to unit-test DocumentDB samples without a live cluster: use the DocumentDB local gateway or mongomock and a mocked LLM client.
- **Where the agent looked:** Searched local-deployment skill and quickstarts; no example unit tests shipped for samples.
- **Effect on this build:** No tests were included; the builder did not add unit tests, and verification relied on live cluster runs. This makes CI/PR review harder for contributors who cannot access the cluster.
- **Suggested fix (sample_or_quickstart):** Add a 'tests/' folder template with pytest examples that use mongomock (or the DocumentDB local gateway) and mock LangChain/OpenAI responses, plus a small CI job example that runs these tests without secrets.

## [medium] Model & embedding defaults for samples (discoverability)

- **What was missing:** A canonical statement in agent-kit/docs about recommended default LLM provider/model and an embedding model for DocumentDB sample templates (including the matching embedding dimension so agents can correctly create vector indexes when required).
- **Where the agent looked:** Readiness findings and decisions show the builder defaulted models by model_default; searches for 'embedding model dimensions' were inconclusive for a canonical default.
- **Effect on this build:** The builder made model-default choices (D007, D023) internally; inconsistent defaults appear across artifacts (.env.example vs agent.py). This leads to inconsistent .env and code defaults and risks incorrect embedding dims if vectors are later added.
- **Suggested fix (discoverability):** An agent-kit rule + short page 'Recommended LLM and embedding defaults for DocumentDB samples' listing a vendor + model pair (OpenAI text-embedding-3-small for embeddings, gpt-4o-mini or gpt-3.5-turbo for reasoning), embedding dims for each model and explicit guidance on how to override via env vars.

## [medium] Vector index createIndexes JSON snippet

- **What was missing:** A concise, copy‑paste 'createIndexes' JSON snippet for IVF/HNSW/DiskANN with example values (dimensions, similarity metric, lBuild/lSearch) in the documentdb-vector-search skill.
- **Where the agent looked:** documentdb-vector-search skill; search results show long docs but builders often guessed createIndex shapes and risk failure.
- **Effect on this build:** The sample intentionally avoids vectors. If a builder were to add vectors they might use incorrect createIndex forms and fail against the live cluster.
- **Suggested fix (mcp_tool_or_description):** Add three minimal JSON templates in the vector-search skill: one for vector-ivf, one for vector-hnsw, and one for vector-diskann with parameter explanations and recommended defaults for small/medium/large datasets.

## [medium] Which Azure resource to use for sample IaC

- **What was missing:** A short agent-kit note clarifying which ARM/Bicep/Terraform resource type to use for the vCore-managed DocumentDB offering (Microsoft.DocumentDB/mongoClusters) and showing a minimal Bicep snippet.
- **Where the agent looked:** Readiness findings show confusion between databaseAccounts and mongoClusters and the discovery loaded mongoClusters docs but many developers still target older resource types.
- **Effect on this build:** No infra-as-code shipped. Builders who attempt to add IaC may choose the wrong resource type and fail provisioning.
- **Suggested fix (naming_or_disambiguation):** Add a 'Which resource to use' page to agent-kit showing the Bicep/ARM/Terraform snippet for Microsoft.DocumentDB/mongoClusters (vCore) and map common older databaseAccounts examples to the new resource.

