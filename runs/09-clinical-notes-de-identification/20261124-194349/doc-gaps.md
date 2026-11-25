# Documentation and tooling gaps: 09-clinical-notes-de-identification

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] PHI and external LLMs

- **What was missing:** Authoritative guidance from Azure DocumentDB about whether and how to send PHI/clinical text to external LLM providers (OpenAI) was not found. The sample included a safety note that sample notes are synthetic, but no compliance checklist or recommended mitigations.
- **Where the agent looked:** Searched installed skills and Microsoft Learn for 'Azure DocumentDB OpenAI PHI guidance' and related queries; no clear product-level guidance was found.
- **Effect on this build:** Builder implemented an OpenAI run mode but did not execute it during verification (no OPENAI_API_KEY). Without product guidance, an agent might send PHI to an external LLM without required contractual or technical protections.
- **Suggested fix (learn_doc):** A short guidance page: 'Handling PHI with Azure DocumentDB and external LLMs' covering: (1) statement of whether sending PHI to external LLMs is endorsed, (2) contractual prerequisites (BAA) and recommended commercial protections, (3) recommended mitigations (local pre-filtering, tokenization, minimal context, hashing), (4) sample safe workflow and sample code snippets showing a dry-run and an explicit explicit opt-in step, (5) link to legal/compliance contacts. Priority: high.

## [high] Provisioning example for mongoClusters (IaC)

- **What was missing:** A minimal Bicep/Terraform example that shows Microsoft.DocumentDB/mongoClusters resource usage and conservative default parameters.
- **Where the agent looked:** Microsoft Learn 'mongoClusters' templates and readiness docs; examples exist but the sample lacked a direct repo-local IaC file.
- **Effect on this build:** The sample expects an existing cluster. Without an IaC snippet, users may attempt to use the wrong ARM type (databaseAccounts) or the wrong CLI group, producing errors or provisioning the wrong service.
- **Suggested fix (sample_or_quickstart):** A minimal Bicep file (or Terraform AzAPI example) placed in the repo: parameters for tier (M30), storage, region, and a README section showing how to use az documentdb mongocluster create. Priority: high.

## [high] Retry and backoff guidance (code-level)

- **What was missing:** A short reusable pattern or code snippet for handling transient DB errors and 429-style throttling with exponential backoff and jitter specific to Azure DocumentDB driver behavior.
- **Where the agent looked:** documentdb-connection skill and docs; the skill explains the concept but a short copy-paste snippet for Python/Motor/AsyncMongoClient was not in the sample.
- **Effect on this build:** The sample runs against a live cluster without retry/backoff logic; batch jobs could fail unpredictably under transient throttling or connectivity issues.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a small code snippet in the documentdb-connection skill showing a retry decorator for pymongo/AsyncIOMotorClient that detects transient errors and 429-like responses and uses exponential backoff with jitter. Priority: high.

## [high] Entra ID usage explanation in sample README

- **What was missing:** A short README section explaining if and how to use Microsoft Entra ID (MONGODB-OIDC) for auth, or why a connection string is demonstrated instead.
- **Where the agent looked:** documentdb-security skill and Microsoft Learn 'Connect to Azure DocumentDB using role-based access control' pages; guidance exists but the sample README didn't mention Entra ID.
- **Effect on this build:** Users expecting the sample to show modern auth will not find guidance and may mistakenly embed long-lived credentials. The sample uses connection strings but doesn't state the production best-practice (prefer Entra ID).
- **Suggested fix (discoverability):** Add a short 'Authentication' subsection to README: explain Entra ID option, link to 'how to enable Entra ID on a cluster' and show minimal code or a link to a driver snippet. Priority: high.

## [medium] Beanie driver recommendation discoverability

- **What was missing:** An authoritative, easily findable statement that the official quickstart recommends Beanie 2 + PyMongo AsyncMongoClient (not Motor) for Azure DocumentDB.
- **Where the agent looked:** Microsoft Learn quickstarts and the installed skills' references; the quickstart exists but an agent in the first discovery pass used a model default and chose Beanie 1.x + Motor.
- **Effect on this build:** The builder picked Beanie 1.x + Motor (requirements.txt pins beanie==1.26.0 and motor==3.1.1). That choice is workable for a demo but contradicts the official quickstart and risks runtime incompatibilities on some environments.
- **Suggested fix (discoverability):** Make the Beanie quickstart recommendation more prominent and add a one-line 'Which client to use' note at the top of the quickstart page. Also add a short 'If you must use Beanie 1.x' compatibility note for older samples. Priority: medium.

## [medium] Vector index creation examples (DocumentDB-specific)

- **What was missing:** Quick copy-paste examples showing the exact createIndexes JSON using the cosmosSearch key and cosmosSearchOptions for DiskANN/HNSW/IVF with dimension, m/ef parameters.
- **Where the agent looked:** Installed documentdb-vector-search skill and Microsoft Learn vector-search pages; they exist but the exact minimal example suitable for a sample was not easily found by the builder.
- **Effect on this build:** If a builder attempts to create vector indexes using community names (e.g., knnVector) or the wrong key names, index creation will fail. This sample omitted vector usage, in part because the starter prompt didn't request embeddings.
- **Suggested fix (discoverability):** Add a one-page 'Vector index quick examples' snippet to the vector-search docs with three minimal createIndexes JSON examples (HNSW, IVF, DiskANN) and a 'choose dimensions' note. Priority: medium.

