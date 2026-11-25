# Phase report

100 samples with a run. 94 finished with exit 0; 4 failed; 2 unfinished. Regenerate with `python loop/phase_report.py`.

## Readiness confidence

94 scored. Min 57, median 73, mean 71.5, max 80. Bands: High 80 and above, Medium 60 to 79, Low below 60.

| Vertical | Samples | Mean | Min | Max | High | Medium | Low |
|---|---|---|---|---|---|---|---|
| banking | 20 | 70.5 | 62 | 80 | 2 | 18 | 0 |
| customer-360 | 20 | 70.8 | 57 | 80 | 2 | 17 | 1 |
| fintech | 19 | 71.2 | 58 | 78 | 0 | 18 | 1 |
| healthcare | 18 | 72.9 | 60 | 80 | 1 | 17 | 0 |
| retail | 17 | 72.2 | 66 | 80 | 1 | 16 | 0 |

## What the model got wrong before reading anything

Cold-quiz questions whose answer from memory was wrong, partly wrong or outdated, across 94 readiness reports.

| Question | Wrong in | Share |
|---|---|---|
| Q02 Which Azure CLI command group creates and manages a cluster? Is it in the core CLI or an extension? | 94/94 | 100% |
| Q03 Which Bicep and Terraform resource types deploy a cluster? | 94/94 | 100% |
| Q04 What does a connection string look like: scheme, host suffix, port, and the options it must carry? | 94/94 | 100% |
| Q06 Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID? | 93/94 | 98% |
| Q01 What is the Azure resource provider namespace and resource type of an Azure DocumentDB cluster? | 92/94 | 97% |
| Q09 How are full-text search and hybrid search done? | 92/94 | 97% |
| Q11 How do you run the database locally for development and tests: which image or emulator, and which port? | 92/94 | 97% |
| Q08 Which vector index types are supported, and what does the command that creates one look like? | 91/94 | 96% |
| Q10 Which MongoDB wire protocol or server versions are supported, and which commonly used MongoDB features are not | 86/94 | 91% |
| Q05 How is capacity provisioned and billed: request units, compute tiers with vCores, serverless, or something els | 83/94 | 88% |
| Q15 What engine is underneath, and does that change anything in application code? | 79/94 | 84% |
| Q12 Are change streams supported, and does anything have to be enabled first? | 78/94 | 82% |
| Q14 What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source Document | 78/94 | 82% |
| S04 (sample-specific question in this slot) | 36/94 | 38% |
| S05 (sample-specific question in this slot) | 36/94 | 38% |
| S03 (sample-specific question in this slot) | 36/94 | 38% |
| S02 (sample-specific question in this slot) | 33/94 | 35% |
| S01 (sample-specific question in this slot) | 20/94 | 21% |
| Q13 Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it? | 5/94 | 5% |
| Q07 Which client library should an application use? Is there a service-specific SDK? | 3/94 | 3% |

## Blocked samples

Readiness said the sample cannot be built as written.

- **healthcare-04** (Medical imaging metadata store)
  - Embedding storage format conflict: The sample strictly requires storing embeddings as BSON Binary vectors, but Azure DocumentDB's native vector indexes require vectors to be a number[] (JSON array of numbers). The app, seed script and index creation must be revised: either (A) change the requirement to store embeddings as number[] so cosmosSearch vector indexes can be created and used, or (B) acce
  - OpenAI model unspecified: The sample needs the exact embedding model and its dimensionality so the vector index can be created with the correct 'dimensions' value. Author action: specify OPENAI_MODEL (and desired embedding precision) before index creation.
  - The prompt required storing embeddings as BSON Binary; if the author insists on that format but still wants vector-ivf index demonstration, the sample cannot be implemented as written and must be changed. Author action: change prompt or accept an alternate approach (store as number[]).

## Build and audit

Build status: {'partial': 1, 'completed': 1}. Audit verdict: {'pass_with_findings': 2}.

Most violated practices across audits:

| Practice | Builds |
|---|---|
| IVF numLists sizing | 1 |
| Embedding storage type | 1 |
| Prefer Entra ID for auth | 1 |
| Retries & 429 handling | 1 |
| Verify index availability | 1 |
| Binary artifacts & indexing | 1 |
| Connection tuning | 1 |
| DiskANN tuning | 1 |
| Unique indexes / idempotent seed | 1 |
| Embed metadata | 1 |
| Validate vector dims | 1 |
| Retry semantics | 1 |
| Audit trail: seed counts | 1 |

## Per sample

| Sample | Arm | Title | Reached | Exit | Review | Readiness | Score | Build | Audit | Min |
|---|---|---|---|---|---|---|---|---|---|---|
| banking-01 | default | Anti-money laundering pattern detector | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.4 |
| banking-02 | default | SWIFT message parser & store | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 77 |  |  | 4.3 |
| banking-03 | default | Core banking transaction ledger | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 66 |  |  | 4.4 |
| banking-04 | default | Regulatory reporting orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 68 |  |  | 4.6 |
| banking-05 | default | Branch performance analytics | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.3 |
| banking-06 | default | Collateral management store | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 64 |  |  | 3.9 |
| banking-07 | default | Mortgage application multi-agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.3 |
| banking-08 | default | Interest rate scenario modeler | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 62 |  |  | 4.4 |
| banking-09 | default | Trade settlement tracker | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 69 |  |  | 4.3 |
| banking-10 | default | Wealth management RAG portal | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.6 |
| banking-11 | default | Correspondent banking risk screener | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 3.7 |
| banking-12 | default | Cross-border payment audit trail | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 71 |  |  | 4.4 |
| banking-13 | default | Basel III capital ratio calculator | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 4.5 |
| banking-14 | default | Customer complaint classifier | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 68 |  |  | 4.5 |
| banking-15 | default | Digital onboarding orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.5 |
| banking-16 | default | ATM network status monitor | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.1 |
| banking-17 | default | Stress testing multi-agent runner | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.2 |
| banking-18 | default | Sanctions list screening agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 65 |  |  | 4.5 |
| banking-19 | default | Insider threat detection pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 63 |  |  | 4.2 |
| banking-20 | default | Interest accrual batch processor | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.8 |
| customer-360-01 | default | Unified customer profile store | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.5 |
| customer-360-02 | default | Real-time event stream ingestion | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 78 |  |  | 5.2 |
| customer-360-03 | default | Next-best-action multi-agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 7.4 |
| customer-360-04 | default | Customer journey mapper | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.1 |
| customer-360-05 | default | Churn prediction pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 71 |  |  | 4.4 |
| customer-360-06 | default | Omnichannel interaction history | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 71 |  |  | 3.9 |
| customer-360-07 | default | Voice-of-customer sentiment hub | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 65 |  |  | 4.6 |
| customer-360-08 | default | Dynamic segmentation engine | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 3.8 |
| customer-360-09 | default | Lead scoring agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 68 |  |  | 4.5 |
| customer-360-10 | default | Support ticket RAG assistant | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.2 |
| customer-360-11 | default | Preference center & consent store | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 72 |  |  | 4.4 |
| customer-360-12 | default | CLV prediction pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 64 |  |  | 4.8 |
| customer-360-13 | default | Household grouping & linkage | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 77 |  |  | 3.8 |
| customer-360-14 | default | Hyper-personalized content engine | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.5 |
| customer-360-15 | default | Cohort analysis backend | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 61 |  |  | 4.7 |
| customer-360-16 | default | Multi-touch attribution model | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.9 |
| customer-360-17 | default | AI survey response analyzer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 57 |  |  | 4.6 |
| customer-360-18 | default | 360 data platform (CDP) orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 4.8 |
| customer-360-19 | default | Proactive outreach orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.1 |
| customer-360-20 | default | Identity resolution multi-agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 69 |  |  | 3.9 |
| fintech-01 | default | Fraud detection with vector similarity | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 77 |  |  | 4.4 |
| fintech-02 | default | Transaction categorization agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 66 |  |  | 4.4 |
| fintech-03 | default | Portfolio tracker with live alerts | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 78 |  |  | 5.8 |
| fintech-04 | default | Earnings call RAG assistant | readiness | 7 |  |  |  |  |  | 2.9 |
| fintech-05 | default | KYC document ingestion pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 5.0 |
| fintech-06 | default | Credit risk multi-agent scorer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 69 |  |  | 4.0 |
| fintech-07 | default | Multi-currency ledger | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.6 |
| fintech-08 | default | Regulatory compliance RAG checker | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 4.5 |
| fintech-09 | default | Crypto wallet activity analyzer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 5.9 |
| fintech-10 | default | Expense report auto-categorizer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 69 |  |  | 5.6 |
| fintech-11 | default | Market news sentiment orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 69 |  |  | 4.1 |
| fintech-12 | default | Invoice matching & reconciliation | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.2 |
| fintech-13 | default | Algorithmic trade journal | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.3 |
| fintech-14 | default | Loan origination workflow orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.1 |
| fintech-15 | default | Financial advisor chatbot (RAG) | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 64 |  |  | 4.6 |
| fintech-16 | default | Subscription billing engine | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 78 |  |  | 4.6 |
| fintech-17 | default | ESG scoring pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 78 |  |  | 4.1 |
| fintech-18 | default | Chargeback dispute multi-agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.2 |
| fintech-19 | default | Option chain data store | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 63 |  |  | 4.8 |
| fintech-20 | default | Open banking API cache layer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 58 |  |  | 6.1 |
| healthcare-01 | default | Patient record summarizer (RAG) | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 5.4 |
| healthcare-02 | default | Clinical trial matching orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 71 |  |  | 6.5 |
| healthcare-03 | default | Medication interaction checker | readiness | 7 |  |  |  |  |  | 3.7 |
| healthcare-04 | default | Medical imaging metadata store | readiness | 0 | sufficient_with_assumptions | blocked | 73 |  |  | 5.4 |
| healthcare-05 | default | Appointment scheduling assistant | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.6 |
| healthcare-06 | default | Symptom triage chatbot (RAG) | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 71 |  |  | 5.0 |
| healthcare-07 | default | Lab results aggregator | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.3 |
| healthcare-08 | default | Insurance pre-auth multi-agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 66 |  |  | 4.4 |
| healthcare-09 | default | Clinical notes de-identification | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.7 |
| healthcare-10 | default | Drug formulary semantic search | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 79 |  |  | 4.5 |
| healthcare-11 | default | Care gap identification pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 4.8 |
| healthcare-12 | default | Hospital bed occupancy tracker | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.2 |
| healthcare-13 | default | Chronic disease risk predictor | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 60 |  |  | 4.4 |
| healthcare-14 | default | Telehealth session summarizer | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.8 |
| healthcare-15 | default | Prescription refill agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 4.5 |
| healthcare-16 | default | Population health dashboard backend | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 3.5 |
| healthcare-17 | default | Rare disease literature search | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.6 |
| healthcare-18 | default | Adverse event reporting pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 72 |  |  | 4.9 |
| healthcare-19 | default | Care coordination multi-agent | readiness | 7 |  |  |  |  |  | 2.5 |
| healthcare-20 | default | Provider directory semantic search | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.6 |
| retail-01 | default | Product catalog with vector search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | partial | pass_with_findings | 11.1 |
| retail-02 | default | AI-powered product recommendations | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 12.7 |
| retail-03 | default | Substitute product finder | readiness | None |  |  |  |  |  |  |
| retail-04 | default | Natural language product search | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 80 |  |  | 4.3 |
| retail-05 | default | Shopping cart with real-time inventory | readiness | None |  |  |  |  |  |  |
| retail-06 | default | Order history & timeline agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 66 |  |  | 5.1 |
| retail-07 | default | Customer review sentiment pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 66 |  |  | 5.4 |
| retail-08 | default | Personalized email campaign builder | readiness | 7 |  |  |  |  |  | 3.1 |
| retail-09 | default | Inventory reorder multi-agent system | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.7 |
| retail-10 | default | Multi-tenant storefront SaaS | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 75 |  |  | 4.0 |
| retail-11 | default | Visual similarity search (image embeddin | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 3.9 |
| retail-12 | default | Abandoned cart recovery orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 4.4 |
| retail-13 | default | Product Q&A chatbot (RAG) | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 67 |  |  | 3.9 |
| retail-14 | default | Dynamic pricing engine | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 4.8 |
| retail-15 | default | Supplier & PO management | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.7 |
| retail-16 | default | Loyalty points ledger | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 76 |  |  | 5.8 |
| retail-17 | default | Seasonal trend spotter agent | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 6.1 |
| retail-18 | default | Returns & refund workflow orchestration | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 68 |  |  | 3.9 |
| retail-19 | default | Cross-sell recommendation (Beanie) | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 77 |  |  | 4.8 |
| retail-20 | default | Store locator with geospatial search | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 73 |  |  | 4.7 |
