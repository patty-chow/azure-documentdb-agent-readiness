# Phase 4 filings: consolidated issues and pull requests

62 filings in `findings/phase4/filings/`, each merging the overlapping drafts the reviewer identified (see REVIEW.md). 46 carry status `needs_sme`: a claim in them needs an engineering or docs owner's answer before it goes public; the open questions are listed inside each file. Nothing has been filed. Sample counts come from one experiment run of 100 prompts and are stated as such in every filing.

## The readiness pipeline (abinav2307/azure-documentdb-agent-readiness), file first: these re-baseline the experiment

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [H01](filings/H01-harness-mcp-json-leaves-documentdb-mcp-management-write.md) | P0 | ready | pr | 36 | 1 | 3 | Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored as tool_unavailable |
| [H06](filings/H06-build-stage-can-return-partial-with-zero-files-and-the-.md) | P0 | ready | issue | 5 | 2 | 3 | Build stage can return partial with zero files and the audit still grades the empty tree |
| [H02](filings/H02-harness-add-mongosh-to-the-build-image-mark-it-optional.md) | P1 | ready | pr | 98 | 3 | 1 | Harness: add mongosh to the build image, mark it optional in the readiness inventory, and ask for a 'Verify by hand' README section |
| [H03](filings/H03-readiness-inventory-detect-installed-accelerators-by-co.md) | P1 | ready | pr | 59 | 3 | 4 | Readiness inventory: detect installed accelerators by code so the Agent Kit, MCP server and local container are not reported as missed |
| [H04](filings/H04-readiness-stage-classify-application-design-choices-as-.md) | P1 | ready | pr | 35 | 2 | 3 | Readiness stage: classify application design choices as builder decisions, not learn-docs gaps |
| [H05](filings/H05-starter-prompts-add-shared-schema-seed-deliverable-shap.md) | P1 | ready | issue | 81 | 4 | 3 | Starter prompts: add shared schema/seed, deliverable-shape and gallery-contract blocks, and pin down underspecified prompts |
| [H07](filings/H07-audit-stage-grades-vcore-samples-against-cosmos-db-ru-a.md) | P1 | needs_sme | pr | 57 | 1 | 2 | Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators |
| [H09](filings/H09-build-image-install-bicep-via-az-and-allow-local-az-bic.md) | P1 | ready | pr | 19 | 1 | 2 | Build image: install Bicep via az and allow local az bicep build/lint |
| [H10](filings/H10-tell-builders-which-llm-embedding-provider-deployments-.md) | P1 | ready | pr | 42 | 1 | 3 | Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use |
| [H12](filings/H12-build-prompt-and-audit-require-pinned-dependencies-with.md) | P1 | needs_sme | pr | 18 | 1 | 3 | Build prompt and audit: require pinned dependencies with a lockfile, a valid .env.example and offline tests |
| [H08](filings/H08-harness-python-3-13-venv-breaks-langchain-llamaindex-in.md) | P2 | ready | issue | 8 | 1 | 2 | Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs and the audit charges it to the sample |
| [H11](filings/H11-run-environment-note-and-inventory-state-the-pinning-po.md) | P2 | needs_sme | pr | 8 | 1 | 3 | Run-environment note and inventory: state the pinning policy, env-var presence and shard count |

## Azure/documentdb-agent-kit

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [K01](filings/K01-fix-retrywrites-the-host-suffix-and-the-cli-spelling-in.md) | P0 | needs_sme | pr | 43 | 2 | 3 | Fix retryWrites and the host suffix in connection/SKILL.md, driver-singleton-client.md, security-tls-required.md and local-env-driven-config.md (one canonical connection string) |
| [K02](filings/K02-azure-deployment-skill-name-az-documentdb-mongocluster-.md) | P1 | needs_sme | pr | 97 | 4 | 5 | azure-deployment skill: name az documentdb mongocluster (documentdb extension) as the CLI group, add an extension and per-path tooling preflight, and fix the mongo-cluster typo |
| [K03](filings/K03-connection-and-security-skills-microsoft-entra-id-mongo.md) | P1 | needs_sme | pr | 99 | 6 | 9 | connection and security skills: Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode, with the enable/registration step and runnable per-driver examples |
| [K04](filings/K04-add-one-change-streams-skill-availability-multishard-en.md) | P1 | needs_sme | pr | 83 | 6 | 9 | Add one change-streams skill: availability, multishard enablement, limitations and a durable resume-token consumer |
| [K05](filings/K05-vector-search-skill-number-storage-rule-and-copy-paste-.md) | P1 | needs_sme | pr | 72 | 5 | 4 | vector-search skill: number[] storage rule and copy-paste cosmosSearch index templates (vector-ivf, vector-hnsw, vector-diskann), with $search as the primary query path |
| [K06](filings/K06-vector-search-and-indexing-skills-create-and-verify-ind.md) | P1 | needs_sme | pr | 55 | 3 | 6 | vector-search and indexing skills: create and verify indexes from application code (ensure_vector_index, ensure_indexes lifecycle) |
| [K07](filings/K07-connection-skill-per-language-get-client-factory-with-v.md) | P1 | needs_sme | pr | 85 | 4 | 6 | connection skill: per-language get_client() factory with vCore-correct transient-error retry and bulk-write partial-failure helpers |
| [K08](filings/K08-driver-local-deployment-skills-idempotent-seed-and-bulk.md) | P1 | needs_sme | pr | 15 | 2 | 6 | driver/local-deployment skills: idempotent seed and bulk-load rule with reference seed scripts |
| [K09](filings/K09-local-deployment-skill-offline-test-tiers-mocked-unit-t.md) | P1 | needs_sme | pr | 16 | 2 | 4 | local-deployment skill: offline test tiers (mocked unit tests, env-gated integration tests, local container) |
| [K10](filings/K10-add-a-sample-scaffold-conventions-skill-canonical-env-e.md) | P1 | needs_sme | pr | 74 | 3 | 4 | Add a sample-scaffold conventions skill: canonical .env.example contract, README checklist and helpers |
| [K11](filings/K11-data-modeling-skill-collection-setup-with-jsonschema-va.md) | P1 | needs_sme | pr | 46 | 4 | 3 | data-modeling skill: collection setup with $jsonSchema validators, Decimal128 money, BSON dates, and idempotent atomic writes |
| [K13](filings/K13-state-the-vcore-plus-storage-billing-model-no-request-u.md) | P1 | needs_sme | pr | 88 | 1 | 2 | State the vCore plus storage billing model (no request units) in AGENTS.md and azure-deployment |
| [K14](filings/K14-add-a-which-documentdb-is-this-naming-block-and-retire-.md) | P1 | ready | pr | 82 | 1 | 2 | Add a 'Which DocumentDB is this?' naming block and retire stale 'Cosmos DB for MongoDB vCore' strings |
| [K16](filings/K16-driver-skill-add-a-copy-paste-pymongo-connect-to-azure-.md) | P1 | needs_sme | pr | 1 | 1 | 2 | driver skill: add a copy-paste PyMongo 'Connect to Azure DocumentDB' rule |
| [K17](filings/K17-full-text-search-skill-say-azure-ai-search-is-not-requi.md) | P1 | needs_sme | pr | 67 | 1 | 3 | full-text-search skill: say Azure AI Search is not required for full-text or hybrid search |
| [K18](filings/K18-fts-hybrid-search-add-the-server-side-unionwith-rrf-pip.md) | P1 | needs_sme | pr | 14 | 1 | 3 | fts-hybrid-search: add the server-side $unionWith RRF pipeline and when to prefer it |
| [K20](filings/K20-document-the-serverversion-choice-in-the-azure-deployme.md) | P1 | needs_sme | pr | 52 | 1 | 4 | Document the serverVersion choice in the azure-deployment, connection and driver skills |
| [K21](filings/K21-connection-skill-add-a-what-differs-from-mongodb-compat.md) | P1 | needs_sme | pr | 24 | 1 | 4 | connection skill: add a 'What differs from MongoDB' compatibility block |
| [K22](filings/K22-fix-404-compatibility-links-and-list-commands-not-expos.md) | P1 | needs_sme | pr | 16 | 1 | 3 | Fix 404 compatibility links and list commands not exposed on Azure DocumentDB |
| [K23](filings/K23-local-deployment-add-a-not-this-line-steering-agents-aw.md) | P1 | ready | pr | 22 | 1 | 2 | local-deployment: add a 'Not this' line steering agents away from the Azure Cosmos DB Emulator |
| [K24](filings/K24-mcp-setup-skill-readme-and-installers-stop-presenting-a.md) | P1 | needs_sme | pr | 5 | 1 | 2 | mcp-setup skill, README and installers: stop presenting a localhost URI as the default |
| [K25](filings/K25-let-the-kit-identify-itself-as-installed-front-matter-m.md) | P1 | ready | pr | 23 | 1 | 2 | Let the kit identify itself as installed (front-matter metadata and installer check) |
| [K26](filings/K26-local-deployment-add-a-gateway-quick-start-surfaced-fro.md) | P1 | ready | pr | 15 | 1 | 2 | local-deployment: add a gateway quick start surfaced from AGENTS.md and mcp-setup |
| [K27](filings/K27-document-mongosh-as-an-optional-tool-with-an-mcp-tool-f.md) | P1 | needs_sme | pr | 16 | 1 | 3 | Document mongosh as an optional tool with an MCP-tool fallback |
| [K29](filings/K29-driver-skill-add-a-reproducible-installs-rule-resolve-v.md) | P1 | needs_sme | pr | 11 | 1 | 3 | driver skill: add a reproducible-installs rule (resolve versions from the registry, lock, npm ci / pinned pip) plus a tested-stack matrix |
| [K31](filings/K31-vector-search-add-a-response-shape-rule-return-the-scor.md) | P1 | needs_sme | pr | 7 | 1 | 2 | vector-search: add a response-shape rule (return the score, never raw vectors) |
| [K32](filings/K32-query-optimization-skill-add-before-you-ship-a-query-ru.md) | P1 | needs_sme | pr | 31 | 1 | 4 | query-optimization skill: add 'before you ship a query' rules (projection, $match first, bounded results and pagination, allowDiskUse, anchored regex) |
| [K33](filings/K33-query-optimization-add-an-explain-executionstats-verifi.md) | P1 | needs_sme | pr | 26 | 1 | 3 | query-optimization: add an explain('executionStats') verification template and observability rules |
| [K34](filings/K34-azure-deployment-skill-add-an-author-iac-only-no-deploy.md) | P1 | ready | issue | 100 | 1 | 2 | azure-deployment skill: add an author-IaC-only (no deploy) path |
| [K35](filings/K35-security-skill-add-a-rule-for-sensitive-data-in-ai-llm-.md) | P1 | needs_sme | pr | 15 | 1 | 3 | security skill: add a rule for sensitive data in AI/LLM applications (PHI/PII redaction, no secrets in prompts, app-layer authorization) |
| [K36](filings/K36-build-time-skills-should-direct-the-agent-to-use-an-ava.md) | P1 | ready | issue | 12 | 1 | 3 | Build-time skills should direct the agent to use an available DocumentDB MCP server |
| [K12](filings/K12-mcp-setup-skill-name-the-documentdb-mcp-server-as-the-d.md) | P2 | needs_sme | pr | 6 | 2 | 4 | mcp-setup skill: name the documentdb MCP server as the data-plane server and say what the Azure MCP Server covers |
| [K15](filings/K15-driver-skill-add-a-transactions-with-sessions-rule-mong.md) | P2 | needs_sme | pr | 3 | 1 | 3 | driver skill: add a transactions-with-sessions rule (Mongoose, Node, PyMongo) |
| [K19](filings/K19-full-text-search-skill-document-the-preview-enablement-.md) | P2 | needs_sme | pr | 2 | 1 | 3 | full-text-search skill: document the preview-enablement prerequisite and CommandNotSupported fail-fast |
| [K30](filings/K30-add-a-framework-integrations-skill-routing-langchain-an.md) | P2 | needs_sme | pr | 9 | 1 | 6 | Add a framework-integrations skill routing LangChain and LlamaIndex tasks to the official integrations |
| [K37](filings/K37-connection-skill-beanie-2-x-runs-on-asyncmongoclient-no.md) | P2 | needs_sme | pr | 3 | 1 | 2 | connection skill: Beanie 2.x runs on AsyncMongoClient, not Motor |
| [K28](filings/K28-mcp-setup-add-an-already-configured-check-and-reconcile.md) | P3 | ready | pr | 1 | 1 | 1 | mcp-setup: add an 'already configured?' check and reconcile the server-entry spelling |

## Microsoft Learn: Azure DocumentDB pages (doc feedback)

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [L01](filings/L01-add-a-driver-and-odm-compatibility-page-with-tested-ver.md) | P0 | needs_sme | learn-feedback | 64 | 3 | 6 | Add a driver and ODM compatibility page with tested versions and client options, linked from every quickstart |
| [L02](filings/L02-vector-search-copy-paste-cosmossearch-index-and-query-h.md) | P1 | needs_sme | learn-feedback | 71 | 3 | 6 | Vector search: copy-paste cosmosSearch index and query how-to, explicit number[] storage rule and embedding-dimensions table |
| [L03](filings/L03-add-a-write-semantics-transactions-and-concurrency-page.md) | P1 | needs_sme | learn-feedback | 42 | 2 | 7 | Add a write semantics, transactions and concurrency page for Azure DocumentDB (retrywrites, write concern, idempotency) |
| [L04](filings/L04-add-a-bulk-and-idempotent-data-ingestion-how-to.md) | P1 | needs_sme | learn-feedback | 17 | 2 | 5 | Add a bulk and idempotent data ingestion how-to for Azure DocumentDB |
| [L05](filings/L05-quickstarts-explain-the-srv-connection-string-and-add-a.md) | P1 | needs_sme | learn-feedback | 23 | 2 | 6 | Quickstarts: explain the SRV connection string and add a 'Choose an authentication method' section that surfaces the Entra ID samples |
| [L06](filings/L06-add-a-which-product-and-resource-type-is-this-include-t.md) | P1 | needs_sme | learn-feedback | 49 | 1 | 4 | Add a 'Which product and resource type is this?' include to the Azure DocumentDB overview and quickstarts |
| [L09](filings/L09-add-modeling-and-query-pattern-recipes-for-applications.md) | P1 | needs_sme | learn-feedback | 26 | 1 | 5 | Add modeling and query pattern recipes for applications |
| [L10](filings/L10-add-an-application-data-protection-section-for-sensitiv.md) | P1 | needs_sme | learn-feedback | 20 | 1 | 3 | Add an application data protection section for sensitive data and LLM pipelines |
| [L11](filings/L11-add-a-test-your-azure-documentdb-application-page.md) | P1 | needs_sme | learn-feedback | 58 | 1 | 5 | Add a 'Test your Azure DocumentDB application' page |
| [L07](filings/L07-add-a-tool-agnostic-connection-string-reference-and-a-c.md) | P2 | needs_sme | learn-feedback | 4 | 1 | 7 | Add a tool-agnostic connection-string reference and a credential-capabilities section |
| [L08](filings/L08-small-reference-gaps-on-learn-pages-including-transacti.md) | P2 | needs_sme | learn-feedback | 9 | 1 | 6 | Small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section, no $setWindowFields stage page |

## microsoft/documentdb-mcp

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [M01](filings/M01-gated-write-management-tools-say-so-in-tool-description.md) | P0 | needs_sme | pr | 36 | 3 | 4 | Gated write/management tools: say so in tool descriptions and make the refusal actionable (opt-in location and driver fallback) |

## Azure/azure-cli-extensions

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [X01](filings/X01-az-cosmosdb-mongocluster-help-text-mark-it-superseded-b.md) | P1 | needs_sme | issue | 42 | 1 | 5 | az cosmosdb mongocluster help text: mark it superseded by az documentdb mongocluster and cross-link the two reference pages |
