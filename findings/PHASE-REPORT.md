# Phase report (arm default)

100 samples with a run. 100 finished with exit 0; 0 failed; 0 unfinished. Regenerate with `python loop/phase_report.py`.

## Readiness confidence

100 scored. Min 51, median 72, mean 71.4, max 81. Bands: High 80 and above, Medium 60 to 79, Low below 60.

| Vertical | Samples | Mean | Min | Max | High | Medium | Low |
|---|---|---|---|---|---|---|---|
| banking | 20 | 70.5 | 62 | 80 | 2 | 18 | 0 |
| customer-360 | 20 | 70.8 | 57 | 80 | 2 | 17 | 1 |
| fintech | 20 | 70.8 | 58 | 78 | 0 | 19 | 1 |
| healthcare | 20 | 73.4 | 60 | 80 | 2 | 18 | 0 |
| retail | 20 | 71.3 | 51 | 81 | 2 | 17 | 1 |

## What the model got wrong before reading anything

Cold-quiz questions whose answer from memory was wrong, partly wrong or outdated, across 100 readiness reports.

| Question | Wrong in | Share |
|---|---|---|
| Q02 Which Azure CLI command group creates and manages a cluster? Is it in the core CLI or an extension? | 100/100 | 100% |
| Q03 Which Bicep and Terraform resource types deploy a cluster? | 100/100 | 100% |
| Q04 What does a connection string look like: scheme, host suffix, port, and the options it must carry? | 100/100 | 100% |
| Q06 Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID? | 98/100 | 98% |
| Q09 How are full-text search and hybrid search done? | 98/100 | 98% |
| Q11 How do you run the database locally for development and tests: which image or emulator, and which port? | 98/100 | 98% |
| Q01 What is the Azure resource provider namespace and resource type of an Azure DocumentDB cluster? | 97/100 | 97% |
| Q08 Which vector index types are supported, and what does the command that creates one look like? | 97/100 | 97% |
| Q10 Which MongoDB wire protocol or server versions are supported, and which commonly used MongoDB features are not | 90/100 | 90% |
| Q05 How is capacity provisioned and billed: request units, compute tiers with vCores, serverless, or something els | 88/100 | 88% |
| Q15 What engine is underneath, and does that change anything in application code? | 85/100 | 85% |
| Q12 Are change streams supported, and does anything have to be enabled first? | 82/100 | 82% |
| Q14 What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source Document | 82/100 | 82% |
| S05 (sample-specific question in this slot) | 39/100 | 39% |
| S03 (sample-specific question in this slot) | 38/100 | 38% |
| S04 (sample-specific question in this slot) | 36/100 | 36% |
| S02 (sample-specific question in this slot) | 36/100 | 36% |
| S01 (sample-specific question in this slot) | 20/100 | 20% |
| Q13 Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it? | 6/100 | 6% |
| Q07 Which client library should an application use? Is there a service-specific SDK? | 3/100 | 3% |

## Blocked samples

Readiness said the sample cannot be built as written.

- **healthcare-04** (Medical imaging metadata store)
  - Embedding storage format conflict: The sample strictly requires storing embeddings as BSON Binary vectors, but Azure DocumentDB's native vector indexes require vectors to be a number[] (JSON array of numbers). The app, seed script and index creation must be revised: either (A) change the requirement to store embeddings as number[] so cosmosSearch vector indexes can be created and used, or (B) acce
  - OpenAI model unspecified: The sample needs the exact embedding model and its dimensionality so the vector index can be created with the correct 'dimensions' value. Author action: specify OPENAI_MODEL (and desired embedding precision) before index creation.
  - The prompt required storing embeddings as BSON Binary; if the author insists on that format but still wants vector-ivf index demonstration, the sample cannot be implemented as written and must be changed. Author action: change prompt or accept an alternate approach (store as number[]).

## Build and audit

Build status: {'completed': 71, 'partial': 29}. Audit verdict: {'pass_with_findings': 97, 'fail': 3}.

Most violated practices across audits:

| Practice | Builds |
|---|---|
| Retries and backoff | 9 |
| Connection tuning | 8 |
| Connection pool tuning | 7 |
| TLS enforcement | 5 |
| Retry on transient errors | 5 |
| Retry/backoff | 4 |
| Retries and idempotency | 4 |
| Optimistic concurrency | 4 |
| Schema validation | 4 |
| Retries & backoff | 4 |
| Retries | 3 |
| Connection timeouts | 3 |
| Explain plans | 3 |
| Retry semantics | 3 |
| Vector index creation | 3 |

## Per sample

| Sample | Arm | Title | Reached | Exit | Review | Readiness | Score | Build | Audit | Min |
|---|---|---|---|---|---|---|---|---|---|---|
| banking-01 | default | Anti-money laundering pattern detector | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 15.3 |
| banking-02 | default | SWIFT message parser & store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 77 | completed | pass_with_findings | 8.6 |
| banking-03 | default | Core banking transaction ledger | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 66 | completed | pass_with_findings | 14.3 |
| banking-04 | default | Regulatory reporting orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | completed | pass_with_findings | 15.8 |
| banking-05 | default | Branch performance analytics | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 9.7 |
| banking-06 | default | Collateral management store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 64 | completed | pass_with_findings | 36.0 |
| banking-07 | default | Mortgage application multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 17.5 |
| banking-08 | default | Interest rate scenario modeler | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 62 | partial | pass_with_findings | 8.7 |
| banking-09 | default | Trade settlement tracker | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | partial | pass_with_findings | 7.9 |
| banking-10 | default | Wealth management RAG portal | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 70 | completed | pass_with_findings | 5.2 |
| banking-11 | default | Correspondent banking risk screener | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 74 | completed | pass_with_findings | 15.6 |
| banking-12 | default | Cross-border payment audit trail | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 71 | completed | pass_with_findings | 11.2 |
| banking-13 | default | Basel III capital ratio calculator | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | completed | pass_with_findings | 29.1 |
| banking-14 | default | Customer complaint classifier | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | partial | pass_with_findings | 14.3 |
| banking-15 | default | Digital onboarding orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 16.1 |
| banking-16 | default | ATM network status monitor | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | partial | pass_with_findings | 11.2 |
| banking-17 | default | Stress testing multi-agent runner | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | partial | pass_with_findings | 13.0 |
| banking-18 | default | Sanctions list screening agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 65 | completed | pass_with_findings | 31.3 |
| banking-19 | default | Insider threat detection pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 63 | partial | pass_with_findings | 16.5 |
| banking-20 | default | Interest accrual batch processor | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 8.3 |
| customer-360-01 | default | Unified customer profile store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | partial | pass_with_findings | 8.9 |
| customer-360-02 | default | Real-time event stream ingestion | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 78 | partial | pass_with_findings | 8.2 |
| customer-360-03 | default | Next-best-action multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | completed | pass_with_findings | 13.0 |
| customer-360-04 | default | Customer journey mapper | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 17.7 |
| customer-360-05 | default | Churn prediction pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 71 | partial | pass_with_findings | 9.6 |
| customer-360-06 | default | Omnichannel interaction history | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 71 | completed | pass_with_findings | 7.9 |
| customer-360-07 | default | Voice-of-customer sentiment hub | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 65 | completed | pass_with_findings | 18.7 |
| customer-360-08 | default | Dynamic segmentation engine | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 11.6 |
| customer-360-09 | default | Lead scoring agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | completed | pass_with_findings | 11.7 |
| customer-360-10 | default | Support ticket RAG assistant | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 19.5 |
| customer-360-11 | default | Preference center & consent store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 72 | completed | pass_with_findings | 14.2 |
| customer-360-12 | default | CLV prediction pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 64 | completed | pass_with_findings | 10.2 |
| customer-360-13 | default | Household grouping & linkage | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 77 | completed | pass_with_findings | 17.3 |
| customer-360-14 | default | Hyper-personalized content engine | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 70 | partial | pass_with_findings | 12.7 |
| customer-360-15 | default | Cohort analysis backend | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 61 | completed | pass_with_findings | 9.3 |
| customer-360-16 | default | Multi-touch attribution model | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.9 |
| customer-360-17 | default | AI survey response analyzer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 57 | completed | pass_with_findings | 13.3 |
| customer-360-18 | default | 360 data platform (CDP) orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | partial | pass_with_findings | 9.5 |
| customer-360-19 | default | Proactive outreach orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 11.5 |
| customer-360-20 | default | Identity resolution multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | completed | pass_with_findings | 15.3 |
| fintech-01 | default | Fraud detection with vector similarity | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 77 | partial | pass_with_findings | 8.7 |
| fintech-02 | default | Transaction categorization agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 66 | partial | pass_with_findings | 11.1 |
| fintech-03 | default | Portfolio tracker with live alerts | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 78 | completed | pass_with_findings | 13.3 |
| fintech-04 | default | Earnings call RAG assistant | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 64 | partial | pass_with_findings | 10.7 |
| fintech-05 | default | KYC document ingestion pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | partial | pass_with_findings | 8.0 |
| fintech-06 | default | Credit risk multi-agent scorer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | completed | pass_with_findings | 9.4 |
| fintech-07 | default | Multi-currency ledger | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 70 |  |  | 4.6 |
| fintech-08 | default | Regulatory compliance RAG checker | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | partial | pass_with_findings | 10.3 |
| fintech-09 | default | Crypto wallet activity analyzer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 11.7 |
| fintech-10 | default | Expense report auto-categorizer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | completed | pass_with_findings | 13.3 |
| fintech-11 | default | Market news sentiment orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | completed | pass_with_findings | 9.8 |
| fintech-12 | default | Invoice matching & reconciliation | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 12.6 |
| fintech-13 | default | Algorithmic trade journal | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 16.5 |
| fintech-14 | default | Loan origination workflow orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 70 | partial | pass_with_findings | 12.3 |
| fintech-15 | default | Financial advisor chatbot (RAG) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 64 | partial | pass_with_findings | 26.4 |
| fintech-16 | default | Subscription billing engine | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 78 | completed | pass_with_findings | 7.6 |
| fintech-17 | default | ESG scoring pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 78 | completed | pass_with_findings | 10.3 |
| fintech-18 | default | Chargeback dispute multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 50.0 |
| fintech-19 | default | Option chain data store | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 63 | completed | pass_with_findings | 14.0 |
| fintech-20 | default | Open banking API cache layer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 58 | completed | pass_with_findings | 7.2 |
| healthcare-01 | default | Patient record summarizer (RAG) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 74 | partial | pass_with_findings | 24.5 |
| healthcare-02 | default | Clinical trial matching orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 71 | completed | pass_with_findings | 8.7 |
| healthcare-03 | default | Medication interaction checker | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 9.9 |
| healthcare-04 | default | Medical imaging metadata store | audit | 0 | sufficient_with_assumptions | blocked | 73 | completed | pass_with_findings | 8.6 |
| healthcare-05 | default | Appointment scheduling assistant | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 4.4 |
| healthcare-06 | default | Symptom triage chatbot (RAG) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 71 | completed | pass_with_findings | 12.1 |
| healthcare-07 | default | Lab results aggregator | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 11.7 |
| healthcare-08 | default | Insurance pre-auth multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 66 | completed | pass_with_findings | 9.5 |
| healthcare-09 | default | Clinical notes de-identification | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 9.1 |
| healthcare-10 | default | Drug formulary semantic search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 79 | partial | pass_with_findings | 9.1 |
| healthcare-11 | default | Care gap identification pipeline | readiness | 0 | sufficient_with_assumptions | ready_with_gaps | 74 |  |  | 4.8 |
| healthcare-12 | default | Hospital bed occupancy tracker | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 9.5 |
| healthcare-13 | default | Chronic disease risk predictor | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 60 | partial | pass_with_findings | 6.5 |
| healthcare-14 | default | Telehealth session summarizer | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 9.4 |
| healthcare-15 | default | Prescription refill agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | completed | pass_with_findings | 16.4 |
| healthcare-16 | default | Population health dashboard backend | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 74 | completed | pass_with_findings | 6.2 |
| healthcare-17 | default | Rare disease literature search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 16.0 |
| healthcare-18 | default | Adverse event reporting pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 72 | completed | pass_with_findings | 7.4 |
| healthcare-19 | default | Care coordination multi-agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | partial | pass_with_findings | 10.3 |
| healthcare-20 | default | Provider directory semantic search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 10.7 |
| retail-01 | default | Product catalog with vector search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | partial | pass_with_findings | 11.1 |
| retail-02 | default | AI-powered product recommendations | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 12.7 |
| retail-03 | default | Substitute product finder | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 81 | partial | pass_with_findings | 9.1 |
| retail-04 | default | Natural language product search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 80 | completed | pass_with_findings | 15.2 |
| retail-05 | default | Shopping cart with real-time inventory | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 78 | completed | pass_with_findings | 10.7 |
| retail-06 | default | Order history & timeline agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 66 | completed | pass_with_findings | 13.6 |
| retail-07 | default | Customer review sentiment pipeline | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 69 | completed | pass_with_findings | 25.9 |
| retail-08 | default | Personalized email campaign builder | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | partial | pass_with_findings | 5.2 |
| retail-09 | default | Inventory reorder multi-agent system | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | completed | pass_with_findings | 13.5 |
| retail-10 | default | Multi-tenant storefront SaaS | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 75 | completed | pass_with_findings | 7.5 |
| retail-11 | default | Visual similarity search (image embeddin | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 67 | partial | pass_with_findings | 12.3 |
| retail-12 | default | Abandoned cart recovery orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 51 | completed | pass_with_findings | 9.4 |
| retail-13 | default | Product Q&A chatbot (RAG) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 70 | partial | pass_with_findings | 22.3 |
| retail-14 | default | Dynamic pricing engine | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 18.0 |
| retail-15 | default | Supplier & PO management | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | partial | pass_with_findings | 13.5 |
| retail-16 | default | Loyalty points ledger | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 76 | completed | pass_with_findings | 8.7 |
| retail-17 | default | Seasonal trend spotter agent | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 18.3 |
| retail-18 | default | Returns & refund workflow orchestration | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 68 | completed | pass_with_findings | 12.6 |
| retail-19 | default | Cross-sell recommendation (Beanie) | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 65 | completed | pass_with_findings | 20.8 |
| retail-20 | default | Store locator with geospatial search | audit | 0 | sufficient_with_assumptions | ready_with_gaps | 73 | completed | pass_with_findings | 10.3 |
