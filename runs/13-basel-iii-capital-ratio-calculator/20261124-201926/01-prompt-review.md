# 1. Prompt review: 13-basel-iii-capital-ratio-calculator

**Verdict: sufficient_with_assumptions**

The starter prompt is specific about the business goal (a Python LangChain agent that runs a DocumentDB aggregation, computes Basel III ratios, and writes a board-ready commentary). Several engineering details (Python version, exact MongoDB driver version, model choice, data/schema shape, seed data, README/run/test scaffolding, infra-as-code, and repo conventions) are not specified and will be decided by the builder or covered by installed skills. No single blocking omission prevents starting the build.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 3: Driver and version, Target service and tier, Authentication and secrets |
| Ambiguous: builder will guess | 4: Language and runtime, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 7: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A .env.example lists every setting with placeholder values — not specified in the prompt or skills; builder must add it deliberately.
- The vector index dimensions match the embedding model's output — the prompt doesn't require embeddings; at risk if gallery requires vector consistency.
- The vector index parameters are chosen for the sample's data size and README explains how to change them — not requested in prompt; at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt doesn't mention seed script; at risk.
- "/search" returns a clear error for an empty query and when the embedding call fails — search API behavior not requested; at risk.
- Search results include the similarity score — search not part of prompt; at risk.
- Dependencies are pinned in requirements.txt — not specified; at risk.
- Unit tests run without a live cluster — not requested; at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt does not request infra-as-code; at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — not specified, so may be incomplete unless the builder adds it.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — prompt says "DocumentDB" but doesn't mandate exact naming; risk the implementer uses other names if not guided.

## Questions for the prompt author

- When you say "Using the DocumentDB skill", do you mean a specific installed skill (which one) or generally use the set of documentdb-* skills? Which should the builder prefer?
- Which LLM/model should the LangChain agent use (provider and model name)? Should the sample assume OpenAI (OPENAI_API_KEY) or a different provider? This affects prompt templates and env var names.
- Should the sample include an idempotent seed script and pinned requirements.txt and a README with run/test instructions and infra-as-code (Bicep/Terraform) examples, or should it be minimal (agent + aggregation + commentary) that runs against the existing cluster?

## Contradictions and missing references

- The starter prompt says "Using the DocumentDB skill" but no single installed skill is named exactly "DocumentDB skill". Many documentdb-* skills are installed; the prompt likely means "use the DocumentDB-related skill(s)" but the phrase could confuse an autonomous builder.
- skill_md run environment states a vector-capable cluster exists, but the prompt does not ask for any vector/embedding functionality; reference requirements expect vector-index matching embedding dims (not mentioned in the prompt).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "...build a Python LangChain agent with a DocumentDB aggregation tool that sums risk-weighted assets and capital elements from position documents... instruct the LLM to interpret the computed ratios against Basel III thresholds and generate a board-ready capital adequacy commentary." | - | - | Clear business problem and what the sample should demonstrate. |
| Workflow type | specified | no | "build a Python LangChain agent..." (single LLM-backed agent is requested) | - | - | Prompt asks for a single LangChain agent; the reference requirements also demand a single-agent implementation. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | skill_md (run environment) | Builder will target a current, common Python runtime such as Python 3.10 or 3.11 (virtualenv available per run environment). | Python is specified but no exact version or packaging (venv/Poetry) is given. skill_md indicates 'python' and 'pip' resolve to a virtualenv at run time, which helps but doesn't fix a concrete Python version. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Builder will use the official pymongo driver (e.g. pymongo >=4.3 / 4.x compatible with MongoDB 7.x) and follow the documentdb-driver guidance (singleton MongoClient, connection reuse). | The prompt doesn't name a driver/version. documentdb-driver skill covers best practices (singleton client) and will guide driver choices, but it does not mandate an exact pinned version — the builder must pick one. |
| Target service and tier | covered_by_skill | no | "Using the DocumentDB skill" | documentdb-azure-deployment | Use the live DocumentDB cluster described in the provided run environment (database sample_banking_13, cluster compute tier M30, MongoDB 7.0 wire protocol). The build will not provision a new cluster unless asked. | skill_md run environment explicitly states a reachable M30 cluster and the database name to use; documentdb-azure-deployment covers provisioning if the builder opts to include infra-as-code. |
| Authentication and secrets | covered_by_skill | no | - | skill_md (run environment) | DOCUMENTDB_URI will be read from an environment variable at runtime (per run environment). Model API keys / LLM credentials will be stored in env vars too (e.g., OPENAI_API_KEY), and no secret values will be committed. | skill_md explicitly instructs the cluster connection string is in DOCUMENTDB_URI and must not be committed; prompt did not state where model credentials come from, so builder will default to env vars. |
| Data model | ambiguous | no | "position documents" and "sums risk-weighted assets and capital elements" | documentdb-data-modeling | Builder will create/use a collection (likely named 'positions') in database 'sample_banking_13' with numeric fields like risk_weighted_assets (rwa), cet1 (CET1 capital), and total_capital (or similar). A schemaVersion field may be added per data-modeling guidance. | Prompt describes intent but not exact document shape, collection name, field names, or whether values are nested — documentdb-data-modeling supplies modeling guidance but not a concrete schema. The builder will choose a simple flat schema for the sample. |
| Sample data | missing | no | - | - | Builder will include a small, idempotent seed script (e.g., seed_data.py or seed.json loader) that inserts a handful (~10–100) of sample 'position' documents with varied RWAs and capital amounts; the script will upsert to avoid duplicates. | Prompt does not mention sample data source, size, license, or how to load it. Reference requirements expect a seed script; none is requested explicitly here. |
| Queries and indexes | ambiguous | no | "DocumentDB aggregation tool that sums risk-weighted assets and capital elements" | documentdb-indexing | The builder will implement the aggregation pipeline (a $group stage with $sum accumulators) and likely rely on the default _id index; no special indexes are strictly required for a full-collection aggregation, but the builder may add single-field indexes on filter fields if any are used. | Prompt requires the aggregation but gives no index guidance. documentdb-indexing skill can be used to add or recommend indexes if the sample shows longer-running queries or filters. |
| AI components | missing | no | "Use prompt engineering to instruct the LLM to interpret the computed ratios against Basel III thresholds" | - | Builder will call an LLM via LangChain (e.g., OpenAI's chat model) and place model credentials in env vars like OPENAI_API_KEY. The sample will not require embeddings or vector indexes unless the author chooses to add reference retrieval. | No specific LLM model (provider or name), nor embedding model/dimensions, are specified. This will be decided by the implementer. |
| App surface | ambiguous | no | - | - | Builder will implement a simple CLI script (e.g., main.py) that runs the LangChain agent end-to-end and prints the board-ready commentary. Alternatively, a minimal HTTP endpoint could be added, but CLI is the likely default. | Prompt does not specify CLI vs API vs UI; the core requirement is an agent producing commentary, which a CLI satisfies and is simplest for a sample. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Builder will not attempt to provision a cluster by default and will use the live cluster provided in the run environment. If infra-as-code is desired, the documentdb-azure-deployment skill provides Bicep/CLI/Terraform templates, but the prompt didn't request them. | Prompt references a 'DocumentDB skill' but does not ask for infra. Reference requirements expect infra-as-code but starter prompt does not. |
| Run and test instructions | missing | no | - | - | Builder will add a README explaining pip install -r requirements.txt, setting DOCUMENTDB_URI and LLM API key env vars, running seed script, then running python main.py to produce the commentary. Tests may be left for later unless requested. | No run/test commands are present in the prompt. |
| Definition of done | missing | no | - | - | Builder will treat the sample as done when: (1) agent runs, (2) aggregation executes against the configured database and returns totals, (3) ratios are computed, and (4) the LLM returns a board-ready commentary referencing Basel III thresholds. | Prompt doesn't list explicit acceptance criteria; the above is the natural interpretation. |
| Constraints and non-goals | missing | no | - | - | Builder will avoid committing secrets, will not provision production infrastructure by default, and will keep sample data small to limit costs. No compliance or certification work is expected for the sample. | No explicit cost / compliance constraints in the prompt. |
| Repository conventions | missing | no | - | - | Builder will use a simple layout: README.md, main.py (agent), tools/aggregation_tool.py, seed_data.py, requirements.txt (pinned), .env.example, tests/ (unit tests). Use 'Azure DocumentDB' in docs per gallery conventions. | No layout or naming conventions are specified in the prompt; skill_md and other skills imply certain practices but do not mandate repo structure. |
