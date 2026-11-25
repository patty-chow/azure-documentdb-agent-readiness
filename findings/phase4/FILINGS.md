# Phase 4 filings: consolidated issues and pull requests

43 filings in `findings/phase4/filings/`, each merging the overlapping drafts the reviewer identified (see REVIEW.md); first-pass filings that were merged again are archived in `filings/merged/`. 26 carry status `needs_sme`: a claim in them needs an engineering or docs owner's answer before it goes public; the open questions are listed inside each file. Nothing has been filed. Sample counts come from one experiment run of 100 prompts and are stated as such in every filing.

## The readiness pipeline (abinav2307/azure-documentdb-agent-readiness): ON HOLD, nothing is filed against the harness for now (owner decision 2026-11-25); share with its owner informally

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [H01](filings/H01-harness-mcp-json-leaves-documentdb-mcp-management-write.md) | P0 | needs_sme | pr | 36 | 1 | 3 | Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored as tool_unavailable |
| [H06](filings/H06-build-stage-can-return-partial-with-zero-files-and-the-.md) | P0 | ready | issue | 5 | 2 | 3 | Build stage can return partial with zero files and the audit still grades the empty tree |
| [H02](filings/H02-harness-add-mongosh-to-the-build-image-mark-it-optional.md) | P1 | ready | pr | 98 | 3 | 1 | Harness: add mongosh to the build image, mark it optional in the readiness inventory, and ask for a 'Verify by hand' README section |
| [H03](filings/H03-readiness-inventory-detect-installed-accelerators-by-co.md) | P1 | ready | pr | 59 | 3 | 3 | Readiness inventory: detect installed accelerators by code so the Agent Kit, MCP server and local container are not reported as missed |
| [H04](filings/H04-readiness-stage-classify-application-design-choices-as-.md) | P1 | ready | pr | 35 | 2 | 3 | Readiness stage: classify application design choices as builder decisions, not learn-docs gaps |
| [H05](filings/H05-starter-prompts-add-shared-schema-seed-deliverable-shap.md) | P1 | ready | issue | 81 | 4 | 3 | Starter prompts: add shared schema/seed, deliverable-shape and gallery-contract blocks, and pin down underspecified prompts |
| [H07](filings/H07-audit-stage-grades-vcore-samples-against-cosmos-db-ru-a.md) | P1 | ready | pr | 57 | 1 | 0 | Audit stage grades vCore samples against Cosmos DB RU-API practices and unrequested accelerators |
| [H09](filings/H09-build-image-install-bicep-via-az-and-allow-local-az-bic.md) | P1 | ready | pr | 19 | 1 | 1 | Build image: install Bicep via az and allow local az bicep build/lint |
| [H10](filings/H10-tell-builders-which-llm-embedding-provider-deployments-.md) | P1 | ready | pr | 42 | 1 | 3 | Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use |
| [H12](filings/H12-build-prompt-and-audit-require-pinned-dependencies-with.md) | P1 | ready | pr | 18 | 1 | 1 | Build prompt and audit: require pinned dependencies with a lockfile, a valid .env.example and offline tests |
| [H08](filings/H08-harness-python-3-13-venv-breaks-langchain-llamaindex-in.md) | P2 | ready | issue | 8 | 1 | 2 | Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs and the audit charges it to the sample |
| [H11](filings/H11-run-environment-note-and-inventory-state-the-pinning-po.md) | P2 | needs_sme | pr | 8 | 1 | 2 | Run-environment note and inventory: state the pinning policy, env-var presence and shard count |

## Azure/documentdb-agent-kit

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [K01](filings/K01-fix-retrywrites-the-host-suffix-and-the-cli-spelling-in.md) | P0 | ready | pr | 43 | 2 | 0 | Fix retryWrites and the host suffix in connection/SKILL.md, driver-singleton-client.md, security-tls-required.md and local-env-driven-config.md (one canonical connection string) |
| [K03](filings/K03-merged.md) | P1 | needs_sme | pr | 99 | 7 | 3 | security and connection skills: Microsoft Entra ID (MONGODB-OIDC) data-plane auth with runnable per-driver examples, and a rule for sensitive data in AI/LLM applications (merges - K03 - K35) |
| [K04](filings/K04-add-one-change-streams-skill-availability-multishard-en.md) | P1 | needs_sme | pr | 83 | 6 | 7 | Add one change-streams skill: availability, multishard enablement, limitations and a durable resume-token consumer |
| [K05](filings/K05-merged.md) | P1 | needs_sme | pr | 73 | 9 | 4 | vector-search skill: number[] storage rule, copy-paste IVF/HNSW/DiskANN index templates with $search as the primary query path, idempotent ensure-index from app code, and a response-shape rule (score, no raw vectors) (merges - K05 - K06 - K31) |
| [K07](filings/K07-merged.md) | P1 | needs_sme | pr | 85 | 9 | 7 | connection and driver skills: get_client() factory with vCore-correct retry and bulk-write helpers, a 'What differs from MongoDB' block, Beanie 2.x on AsyncMongoClient, transactions with sessions, a copy-paste PyMongo connect rule, and reproducible installs (merges - K07 - K21 - K37 - K29 - K15 - K16) |
| [K10](filings/K10-add-a-sample-scaffold-conventions-skill-canonical-env-e.md) | P1 | ready | pr | 74 | 3 | 2 | Add a sample-scaffold conventions skill: canonical .env.example contract, README checklist and helpers |
| [K11](filings/K11-data-modeling-skill-collection-setup-with-jsonschema-va.md) | P1 | needs_sme | pr | 46 | 4 | 1 | data-modeling skill: collection setup with $jsonSchema validators, Decimal128 money, BSON dates, and idempotent atomic writes |
| [K13](filings/K13-merged.md) | P1 | needs_sme | pr | 96 | 2 | 2 | Add a 'Which DocumentDB is this?' naming block, state the vCore plus storage billing model (no request units), and retire stale 'Cosmos DB for MongoDB vCore' strings (merges - K13 - K14) |
| [K17](filings/K17-merged.md) | P1 | needs_sme | pr | 73 | 3 | 1 | full-text-search skill: Azure AI Search is not required, document preview enablement with CommandNotSupported fail-fast, and add the server-side $unionWith RRF hybrid pipeline (merges - K17 - K18 - K19) |
| [K20](filings/K20-document-the-serverversion-choice-in-the-azure-deployme.md) | P1 | needs_sme | pr | 52 | 1 | 3 | Document the serverVersion choice in the azure-deployment, connection and driver skills |
| [K22](filings/K22-fix-404-compatibility-links-and-list-commands-not-expos.md) | P1 | needs_sme | pr | 16 | 1 | 1 | Fix 404 compatibility links and list commands not exposed on Azure DocumentDB |
| [K23](filings/K23-merged.md) | P1 | ready | pr | 55 | 6 | 7 | local-deployment skill: steer agents away from the Cosmos DB Emulator, add a gateway quick start, offline test tiers, and an idempotent seed and bulk-load rule (merges - K23 - K09 - K08 - K26) |
| [K25](filings/K25-let-the-kit-identify-itself-as-installed-front-matter-m.md) | P1 | ready | pr | 23 | 1 | 2 | Let the kit identify itself as installed (front-matter metadata and installer check) |
| [K27](filings/K27-merged.md) | P1 | needs_sme | pr | 27 | 5 | 7 | mcp-setup skill: name the documentdb MCP server as the data-plane server, stop defaulting to a localhost URI, add an 'already configured?' check, and document mongosh as optional with an MCP-tool fallback (merges - K27 - K12 - K24 - K28) |
| [K32](filings/K32-merged.md) | P1 | needs_sme | pr | 45 | 2 | 3 | query-optimization skill: 'before you ship a query' rules (projection, $match first, bounded results, per-tier memory bounds instead of allowDiskUse, anchored regex) and an explain('executionStats') verification template (merges - K32 - K33) |
| [K34](filings/K34-merged.md) | P1 | ready | pr | 100 | 5 | 2 | azure-deployment skill: name az documentdb mongocluster as the CLI group with a tooling preflight, fix the mongo-cluster typo, and add an author-IaC-only (no deploy) path (merges - K34 - K02) |
| [K36](filings/K36-build-time-skills-should-direct-the-agent-to-use-an-ava.md) | P1 | ready | issue | 12 | 1 | 3 | Build-time skills should direct the agent to use an available DocumentDB MCP server |
| [K30](filings/K30-add-a-framework-integrations-skill-routing-langchain-an.md) | P2 | needs_sme | pr | 9 | 1 | 3 | Add a framework-integrations skill routing LangChain and LlamaIndex tasks to the official integrations |

## Microsoft Learn: Azure DocumentDB pages (doc feedback)

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [L01](filings/L01-add-a-driver-and-odm-compatibility-page-with-tested-ver.md) | P0 | needs_sme | learn-feedback | 64 | 3 | 5 | Add a driver and ODM compatibility page with tested versions and client options, linked from every quickstart |
| [L02](filings/L02-vector-search-copy-paste-cosmossearch-index-and-query-h.md) | P1 | needs_sme | learn-feedback | 71 | 3 | 2 | Vector search: copy-paste cosmosSearch index and query how-to, explicit number[] storage rule and embedding-dimensions table |
| [L03](filings/L03-add-a-write-semantics-transactions-and-concurrency-page.md) | P1 | needs_sme | learn-feedback | 42 | 2 | 7 | Add a write semantics, transactions and concurrency page for Azure DocumentDB (retrywrites, write concern, idempotency) |
| [L04](filings/L04-add-a-bulk-and-idempotent-data-ingestion-how-to.md) | P1 | needs_sme | learn-feedback | 17 | 2 | 2 | Add a bulk and idempotent data ingestion how-to for Azure DocumentDB |
| [L05](filings/L05-quickstarts-explain-the-srv-connection-string-and-add-a.md) | P1 | needs_sme | learn-feedback | 23 | 2 | 2 | Quickstarts: explain the SRV connection string and add a 'Choose an authentication method' section that surfaces the Entra ID samples |
| [L06](filings/L06-add-a-which-product-and-resource-type-is-this-include-t.md) | P1 | needs_sme | learn-feedback | 49 | 1 | 1 | Add a 'Which product and resource type is this?' include to the Azure DocumentDB overview and quickstarts |
| [L09](filings/L09-add-modeling-and-query-pattern-recipes-for-applications.md) | P1 | needs_sme | learn-feedback | 26 | 1 | 2 | Add modeling and query pattern recipes for applications |
| [L10](filings/L10-add-an-application-data-protection-section-for-sensitiv.md) | P1 | needs_sme | learn-feedback | 20 | 1 | 2 | Add an application data protection section for sensitive data and LLM pipelines |
| [L11](filings/L11-add-a-test-your-azure-documentdb-application-page.md) | P1 | needs_sme | learn-feedback | 58 | 1 | 3 | Add a 'Test your Azure DocumentDB application' page |
| [L07](filings/L07-add-a-tool-agnostic-connection-string-reference-and-a-c.md) | P2 | needs_sme | learn-feedback | 4 | 1 | 5 | Add a tool-agnostic connection-string reference and a credential-capabilities section |
| [L08](filings/L08-small-reference-gaps-on-learn-pages-including-transacti.md) | P2 | needs_sme | learn-feedback | 9 | 1 | 4 | Small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section, no $setWindowFields stage page |

## microsoft/documentdb-mcp

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [M01](filings/M01-gated-write-management-tools-say-so-in-tool-description.md) | P0 | ready | pr | 36 | 3 | 3 | Gated write/management tools: say so in tool descriptions and make the refusal actionable (opt-in location and driver fallback) |

## Azure/azure-cli-extensions

| Id | Pri | Status | Type | Samples | Drafts merged | Open q. | Title |
|---|---|---|---|---|---|---|---|
| [X01](filings/X01-az-cosmosdb-mongocluster-help-text-mark-it-superseded-b.md) | P1 | needs_sme | issue | 42 | 1 | 2 | az cosmosdb mongocluster help text: mark it superseded by az documentdb mongocluster and cross-link the two reference pages |
