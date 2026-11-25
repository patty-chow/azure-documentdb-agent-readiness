# 1. Prompt review: 01-fraud-detection-with-vector-similarity

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the high-level goal (Python LangChain agent that encodes transactions, stores fraud pattern embeddings in DocumentDB, uses vector search to score and explain fraud risk). The provided skill.md covers the run environment and connection-string handling and the target cluster details. Many lower-level engineering choices (Python version, driver, exact embedding model, API surface, index creation parameters, test/infrastructure artifacts, and README/run instructions) are unspecified and will be chosen by the builder; these are not blocking but will require assumptions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 3: Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 7: Language and runtime, Data model, Sample data, Queries and indexes, AI components, App surface, Repository conventions |
| Missing: builder will guess | 4: Driver and version, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The agent's embedding model choice and credentials come from environment variables (model creds missing): prompt and skill.md do not name the embedding provider or env vars for model credentials; builder will have to choose (at risk).
- .env.example lists every setting with placeholder values: skill.md suggests using .env.example but does not list every required setting; the prompt doesn't require it (at risk).
- Vector index dimensions match the embedding model's output: model not chosen, so dims not specified and must be derived at runtime; risk of mismatch if not handled explicitly.
- Vector index parameters chosen for the sample's data size and README explains how to change them: prompt does not provide parameters or documentation guidance; builder will pick defaults and may not document tuning.
- A LangChain tool performs the vector search against Azure DocumentDB with a $search / cosmosSearch query: the prompt mentions a vector search tool but doesn't require the $search/cosmosSearch API or show the exact query; builder may implement a different access pattern.
- One database client is created and reused across requests: not specified; builder may or may not implement a singleton/shared client.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data: prompt asks to store patterns and skill.md requires loading data for verification but neither mandates an idempotent seed script.
- " /search " returns a clear error for an empty query and when the embedding call fails: error-handling behavior is not specified.
- Search results include the similarity score: prompt asks for similar cases and a risk score but does not require returning individual similarity scores in results.
- Dependencies are pinned in requirements.txt: not specified in prompt or skill.md.
- Unit tests run without a live cluster: no guidance; test strategy is unspecified.
- Infrastructure for the cluster is provided as code: skill.md forbids provisioning and no infra-as-code is requested in prompt; requirement for infra code is at risk.
- README covers what the sample shows, prerequisites, setup, run, and clean-up: not specified in prompt; skill.md expects verification steps but doesn't require full README content.
- The sample uses the name 'Azure DocumentDB' throughout: prompt mentions DocumentDB, but there is no explicit instruction to avoid other product names in repo content; at risk of inconsistent naming.

## Questions for the prompt author

- Which embedding model/provider should the sample use (e.g. OpenAI embeddings, a local transformer, or a specific model name)? This affects dimensions and env vars.
- What app surface do you prefer for the sample: an HTTP API (e.g. FastAPI with /search), a CLI, or a notebook demo? The reference requirements expect a /search route but the prompt does not mandate it.
- Should infrastructure-as-code be included (Bicep/Terraform/azd) to provision the cluster, or must the sample rely exclusively on the existing cluster described in the skill.md? (skill.md currently forbids provisioning another cluster)

## Contradictions and missing references

- The starter prompt says "Using the DocumentDB skill" but the provided <installed_skills> list is empty. A separate skill.md (run environment) is present and must be used to satisfy the prompt; clarify whether a DocumentDB client/tooling skill is expected to be available to the builder.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent that encodes transaction features as embeddings, stores known fraud pattern vectors ... and on each new transaction uses a vector search tool to find similar historical cases. The agent should return a fraud risk score and a natural language explanation of the matching patterns." | - | - | Business problem and demo are stated directly in the prompt. |
| Workflow type | specified | no | "Python LangChain agent" | - | - | Single-agent LangChain workflow is requested. |
| Language and runtime | ambiguous | no | "Python" | skill.md (run environment) | Builder will use a modern Python 3.x (commonly 3.10 or 3.11) virtual environment and target that runtime; pip/venv semantics per skill.md. | Prompt states Python but not the specific version. |
| Driver and version | missing | no | - | skill.md (run environment) | Use PyMongo (pymongo) driver, a current stable 4.x release, pinned in requirements.txt (e.g. pymongo>=4.0,<5.0). | No driver or version is specified; skill.md notes MongoDB wire protocol but not which client to use. |
| Target service and tier | covered_by_skill | no | "DocumentDB vector-ivf index" | skill.md (run environment) | - | skill.md explicitly says a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable and must be used (DATABASE sample_fintech_01). |
| Authentication and secrets | covered_by_skill | no | "Using the DocumentDB skill" | skill.md (run environment) | - | skill.md requires reading connection string from DOCUMENTDB_URI env var and not writing credentials into files; implies secrets stored in environment; model creds are not specified there. |
| Data model | ambiguous | no | "stores known fraud pattern vectors in a DocumentDB vector-ivf index ... each document carrying the pattern information the explanation draws on" | skill.md (run environment) - database name | Builder will create a collection named e.g. 'fraud_patterns' in database sample_fintech_01; documents include fields like _id, pattern_id, embedding (list[float]), description, example_transactions, metadata. No sharding assumed for small sample. | Database name is provided by skill.md; collection name, exact document shape and shard key are not specified. |
| Sample data | ambiguous | no | - | skill.md (run environment) | Include a small synthetic dataset bundled with the repo and a seed script that loads it (e.g. a few dozen pattern documents and a few dozen sample transactions). License: synthetic/mit-like placeholder. | Prompt asks to store known fraud patterns but does not specify source, size, or license. skill.md requires the builder to load sample data for verification but gives no source. |
| Queries and indexes | ambiguous | no | "stores known fraud pattern vectors in a DocumentDB vector-ivf index"; "vector search tool" | skill.md (run environment) - cluster supports IVF/HNSW/DiskANN | Code will create a cosmosSearch vector-ivf index on the embedding field with dimensions equal to the embedding length and use cosine similarity. Index parameters (e.g. nlists, probes) will be set conservatively for a small sample (defaults or small nlists) and documented. | Index kind (vector-ivf) is specified, but exact parameters and code-level API for creating the index are not detailed. |
| AI components | ambiguous | no | "encodes transaction features as embeddings" | - | Builder will use a hosted embedding provider (commonly OpenAI embeddings via LangChain) and obtain model credentials from environment variables (e.g. OPENAI_API_KEY). Exact model chosen (e.g. text-embedding-3-small) will be selected by the builder and dims derived at runtime. | Prompt requires embeddings but gives no model, dimensions, or provider; skill.md doesn't specify model credentials. |
| App surface | ambiguous | no | "A Python LangChain agent is the single entry point: it accepts a new transaction and runs the fraud check for it." (reference requirements) | skill.md (run environment) - agent is entry point | Implement a minimal HTTP API (FastAPI) with a /search or /score endpoint that accepts a transaction JSON payload and returns {risk_score, explanation, matches}. Alternatively, provide a small CLI demo; default will be an API because that is more demonstrable. | Prompt says agent is entry point but does not say whether it's a CLI, API, or web UI; the reference expects an API (/search). |
| Provisioning and deployment | covered_by_skill | no | - | skill.md (run environment) | - | skill.md states a reachable cluster exists and prohibits provisioning another cluster; so the sample should not create cloud infra. The prompt does not request infra-as-code. |
| Run and test instructions | missing | no | - | skill.md (run environment) - verification required | Builder will provide README steps: pip install -r requirements.txt, copy .env.example to .env, run python seed_data.py, then start uvicorn app:app, and show example /search requests. Tests likely run via pytest with some unit tests mocking the DB. | No explicit run commands or test instructions in prompt; skill.md requires verification but doesn't give commands. |
| Definition of done | missing | no | - | - | Definition of done will be: seed script creates collection and index, sample data is loaded, agent accepts transactions and returns numeric risk score and textual explanation, and build report documents what was run. | No explicit acceptance criteria are provided in the prompt. |
| Constraints and non-goals | missing | no | - | skill.md (run environment) - do not provision cluster | Keep sample small to control costs; do not provision new clusters; avoid including real sensitive data. | Prompt doesn't enumerate cost or compliance constraints beyond using the existing cluster. |
| Repository conventions | ambiguous | no | - | skill.md (run environment) - mentions .env.example placeholder | Use conventional layout: src/, tests/, README.md, requirements.txt (pinned), .env.example, seed_data.py, app/main.py. Use 'Azure DocumentDB' in README and code comments. | skill.md suggests .env.example but other repo conventions (pin deps, README content, naming) are not specified. |
