# Phase report (arm control)

10 samples with a run. 10 finished with exit 0; 0 failed; 0 unfinished. Regenerate with `python loop/phase_report.py`.

## Readiness confidence

10 scored. Min 29, median 38, mean 39.6, max 58. Bands: High 80 and above, Medium 60 to 79, Low below 60.

| Vertical | Samples | Mean | Min | Max | High | Medium | Low |
|---|---|---|---|---|---|---|---|
| banking | 2 | 40.5 | 32 | 49 | 0 | 0 | 2 |
| customer-360 | 2 | 48.0 | 38 | 58 | 0 | 0 | 2 |
| fintech | 2 | 33.5 | 29 | 38 | 0 | 0 | 2 |
| healthcare | 2 | 37.0 | 34 | 40 | 0 | 0 | 2 |
| retail | 2 | 39.0 | 36 | 42 | 0 | 0 | 2 |

## What the model got wrong before reading anything

Cold-quiz questions whose answer from memory was wrong, partly wrong or outdated, across 10 readiness reports.

| Question | Wrong in | Share |
|---|---|---|
| Q01 What is the Azure resource provider namespace and resource type of an Azure DocumentDB cluster? | 10/10 | 100% |
| Q02 Which Azure CLI command group creates and manages a cluster? Is it in the core CLI or an extension? | 10/10 | 100% |
| Q04 What does a connection string look like: scheme, host suffix, port, and the options it must carry? | 10/10 | 100% |
| Q06 Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID? | 10/10 | 100% |
| Q10 Which MongoDB wire protocol or server versions are supported, and which commonly used MongoDB features are not | 10/10 | 100% |
| Q11 How do you run the database locally for development and tests: which image or emulator, and which port? | 10/10 | 100% |
| Q03 Which Bicep and Terraform resource types deploy a cluster? | 9/10 | 90% |
| Q08 Which vector index types are supported, and what does the command that creates one look like? | 9/10 | 90% |
| Q09 How are full-text search and hybrid search done? | 9/10 | 90% |
| Q12 Are change streams supported, and does anything have to be enabled first? | 9/10 | 90% |
| Q13 Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it? | 9/10 | 90% |
| S03 (sample-specific question in this slot) | 8/10 | 80% |
| Q05 How is capacity provisioned and billed: request units, compute tiers with vCores, serverless, or something els | 7/10 | 70% |
| S04 (sample-specific question in this slot) | 7/10 | 70% |
| Q14 What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source Document | 6/10 | 60% |
| S05 (sample-specific question in this slot) | 5/10 | 50% |
| Q15 What engine is underneath, and does that change anything in application code? | 5/10 | 50% |
| Q07 Which client library should an application use? Is there a service-specific SDK? | 3/10 | 30% |
| S02 (sample-specific question in this slot) | 3/10 | 30% |
| S01 (sample-specific question in this slot) | 2/10 | 20% |

## Build and audit

Build status: {'completed': 9, 'partial': 1}. Audit verdict: {'pass_with_findings': 10}.

Most violated practices across audits:

| Practice | Builds |
|---|---|
| Prefer server-side vector index | 1 |
| Set vs replace for source attributes | 1 |
| Retry/backoff | 1 |
| DB-level schema validation | 1 |
| Chunk document fields and indexes | 1 |
| retryWrites / idempotent upserts | 1 |
| Persist embedding metadata | 1 |
| Avoid fetching all embeddings | 1 |
| Bulk seed writes | 1 |
| Connection client reuse | 1 |
| Index creation idempotency | 1 |
| Retries/backoff | 1 |
| Server feature detection | 1 |
| Index presence verification | 1 |

## Per sample

| Sample | Arm | Title | Reached | Exit | Review | Readiness | Score | Build | Audit | Min |
|---|---|---|---|---|---|---|---|---|---|---|
| banking-01 | control | Anti-money laundering pattern detector | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 49 | completed | pass_with_findings | 9.2 |
| banking-11 | control | Correspondent banking risk screener | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 32 | completed | pass_with_findings | 11.2 |
| customer-360-01 | control | Unified customer profile store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 58 | completed | pass_with_findings | 9.3 |
| customer-360-11 | control | Preference center & consent store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 38 | completed | pass_with_findings | 9.6 |
| fintech-01 | control | Fraud detection with vector similarity | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 29 | completed | pass_with_findings | 9.2 |
| fintech-11 | control | Market news sentiment orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 38 | completed | pass_with_findings | 10.1 |
| healthcare-01 | control | Patient record summarizer (RAG) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 40 | completed | pass_with_findings | 10.8 |
| healthcare-11 | control | Care gap identification pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 34 | completed | pass_with_findings | 9.3 |
| retail-01 | control | Product catalog with vector search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 36 | completed | pass_with_findings | 11.3 |
| retail-11 | control | Visual similarity search (image embeddin | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 42 | partial | pass_with_findings | 30.0 |
