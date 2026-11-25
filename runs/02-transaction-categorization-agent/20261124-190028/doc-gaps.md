# Documentation and tooling gaps: 02-transaction-categorization-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LLM provider env vars and selection

- **What was missing:** No canonical guidance in the skills on which LLM provider or env var names the agent-kit expects for samples (OpenAI vs Azure OpenAI vs Anthropic).
- **Where the agent looked:** documentdb skills, prompt and readiness artifacts; .env.example exists in repo but this is sample-local, not a kit-level rule.
- **Effect on this build:** The builder defaulted to OpenAI (OPENAI_API_KEY). This is reasonable but inconsistent choices across samples will confuse users and agents when trying to auto-run or verify samples.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: 'When building LangChain JS samples, prefer provider X by default; declare required env vars in .env.example with canonical names (OPENAI_API_KEY for OpenAI, AZURE_OPENAI_KEY for Azure OpenAI). Provide a short code snippet demonstrating how to switch providers.'

## [high] Seed data schema & canonical sample rows

- **What was missing:** No central example of the canonical transaction document schema (field names, currency, amount format, date field name) in kit docs.
- **Where the agent looked:** prompt, README, documentdb-data-modeling skill and discovered_practices searches.
- **Effect on this build:** Builder picked a workable schema (transactionId, merchant, amount, date, category) and the seed script uses those fields; mismatch risks arise if a verifier or another sample expects a different date field name (e.g., transactionDate vs date).
- **Suggested fix (sample_or_quickstart):** Add a small 'sample-data.md' showing the document shape and a JSON example of canonical seed rows, plus a seed script template that other samples can reuse.

## [high] Unit tests that run without cloud

- **What was missing:** No tests or guidance on creating tests that mock Azure DocumentDB (mongodb-memory-server or driver mocks).
- **Where the agent looked:** repo, documentdb-local-deployment skill, and discovered_practices searches.
- **Effect on this build:** The sample ships without tests; that reduces confidence and prevents CI validation in gallery pipelines that cannot hit the live cluster.
- **Suggested fix (sample_or_quickstart):** Add a 'tests' folder with example jest tests using mongodb-memory-server (or driver-mocking) to verify seeding, prompt-to-model mapping (mock LLM), and aggregation pipeline formatting. Include CI snippet to run tests with no cloud access.

## [high] PII / LLM data-handling guidance for samples

- **What was missing:** No explicit sample-level guideline on redacting PII before sending transaction text to external LLMs in the agent kit.
- **Where the agent looked:** documentdb skills and the repository; searches for 'redact PII LLM DocumentDB' returned no authoritative guidance in the kit.
- **Effect on this build:** The sample includes merchant/account text in prompts without redaction. For many datasets this is fine; for others (full names, account numbers) the absence of guidance could lead to accidental leakage.
- **Suggested fix (learn_doc):** A 'privacy when using LLMs' page describing recommended redactions for fintech samples, code snippets to perform canonical redactions, and an example audit log pattern to record prompt inputs (or their checksums).

## [medium] Fixed taxonomy contents

- **What was missing:** No authoritative or recommended taxonomy for transaction categories is documented in the public kit or skills; the sample author chose a taxonomy in code.
- **Where the agent looked:** Starter prompt, documentdb-* skills loaded (documentdb-natural-language-querying referenced), and quicksearches listed in discovered_practices (no useful public taxonomy found).
- **Effect on this build:** The builder picked a reasonable taxonomy (Food, Travel, Utilities, Entertainment, Income, Healthcare, Shopping, Other). This is acceptable for the sample, but other builders may pick inconsistent taxonomies and agents cannot confirm a canonical set.
- **Suggested fix (learn_doc):** A short page 'Suggested taxonomies for transaction categorization' listing recommended taxonomies for common samples (Personal finance: Food, Travel, Utilities, Entertainment, Income, Healthcare, Shopping, Other; Business expense: Travel, Meals, Office, SaaS, Payroll, Refunds). Include a paragraph on choosing granularity and an example JSON snippet to copy into sample code.

## [medium] Dependency pinning policy

- **What was missing:** No kit-level guidance enforcing pinned dependencies or an explicit policy noting that package-lock.json is required for reproducible builds.
- **Where the agent looked:** repo package.json and skills documentation.
- **Effect on this build:** package.json uses caret ranges (^) though a package-lock.json is present. Different builders may check in/out different lockfile policy causing inconsistent installs.
- **Suggested fix (agent_kit_rule):** A short rule: 'All gallery Node samples must include package-lock.json and either use exact versions in package.json or document the lockfile policy. CI should run npm ci to ensure deterministic installs.'

## [medium] Infrastructure-as-code sample for mongoClusters

- **What was missing:** No example Bicep/ARM/Terraform for Microsoft.DocumentDB/mongoClusters provided in the sample repository or kit-level quickstarts.
- **Where the agent looked:** repository and documentdb-azure-deployment skill docs.
- **Effect on this build:** Builder correctly used existing cluster per run policy; a future builder expecting infra-as-code would have to author templates from scratch and might mistakenly target the wrong resource type (databaseAccounts vs mongoClusters).
- **Suggested fix (mcp_tool_or_description):** Ship a small Bicep and Terraform example that creates a minimal Microsoft.DocumentDB/mongoClusters resource with paramized tier/storage/region and guidance to use environment secrets (Key Vault) for credentials. Include notes to avoid confusing 'databaseAccounts' templates.

