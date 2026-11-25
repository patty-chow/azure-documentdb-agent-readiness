# 1. Prompt review: 08-dynamic-segmentation-engine

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Python LangChain agent that calls a DocumentDB aggregation tool to compute recency/frequency/category-affinity, injects segmentation rules into the prompt, assigns a segment label, and writes it back. Many implementation details (Python version, driver version, exact collection / document shapes, embedding/chat models, app surface, seed scripts, infra-as-code, README/test details) are left for the builder to decide; installed skills cover best-practices for drivers, connections, data modeling, indexing and vector search and will steer those defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 6: Language and runtime, Data model, Queries and indexes, AI components, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not explicitly required by the prompt; although skill_md advises env usage, the sample may omit a complete .env.example.
- The vector index dimensions match the embedding model's output — prompt doesn't pick an embedding model; dimension choice is unspecified and thus at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — not specified; indexing guidance exists but the sample may not document tuning.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — starter prompt doesn't require an idempotent seed script; local-deployment skill advises patterns but no concrete script is provided.
- /search returns a clear error for an empty query and when the embedding call fails — the prompt does not require search endpoints or error handling specifics; likely omitted unless the builder adds them.
- Search results include the similarity score — prompt focuses on behavioral aggregation and segmentation, not search result scoring; including similarity scores is not guaranteed.
- Dependencies are pinned in `requirements.txt` — prompt doesn't specify pinning, so builder might not pin versions unless guided by repo conventions.
- Unit tests run without a live cluster — prompt asks to verify against a live cluster; offline-capable unit tests (mocks) are not required and may be missing.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the prompt and skill_md assume a cluster exists and explicitly say not to provision one; infra-as-code is likely not provided.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't ask for a full README; it's at risk of being incomplete.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — prompt uses 'DocumentDB'; the builder needs to ensure consistent naming across README and code to satisfy gallery policy.

## Questions for the prompt author

- Which Python version should the sample target (e.g., 3.10 or 3.11)? This affects dependency pins and CI configuration.
- Which AI provider and specific models (chat and embedding) should the LangChain agent use, and do you want embedding-based vector search included or is it out of scope? (Model choice determines embedding dimension and vector-index parameters.)

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent ... computes behavioural metrics (recency, frequency, category affinity) per customer on demand ... have the agent assign a segment label, writing it back to the customer profile document in DocumentDB." | - | - | Clear single-sentence goal in the starter prompt; skill_md supplements runtime constraints. |
| Workflow type | specified | no | "Python LangChain agent" | - | - | Single-agent LangChain workflow is explicitly requested. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | - | Builder will target a current stable Python 3.x (likely 3.10 or 3.11) and create a venv; requirements pinned to that runtime. | Prompt names Python but does not give a version; skill_md says `python` resolves to a virtual environment but gives no concrete version. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use PyMongo (the MongoDB Python driver) and follow singleton MongoClient pattern; builder will pick a recent PyMongo 4.x release and pin it in requirements.txt. | The documentdb-driver skill prescribes reuse of MongoClient and driver best practices but does not mandate an exact version; the builder will choose a PyMongo 4.x version. |
| Target service and tier | specified | no | - | - | Use the already-provisioned vector-capable Azure DocumentDB cluster described in skill_md (database sample_customer_360_08). | skill_md provides environment: vector-capable cluster, compute tier M30, MongoDB 7.0 wire protocol and DOCUMENTDB_URI env var to use. |
| Authentication and secrets | specified | no | - | - | Connection string is read from environment variable DOCUMENTDB_URI; credentials not committed to repo and a .env.example placeholder used. | skill_md explicitly instructs where the connection string lives and that it must not be written into files or logs. |
| Data model | ambiguous | no | - | documentdb-data-modeling | Builder will create a database `sample_customer_360_08` (specified in skill_md) and at least two collections: `customers` (profile docs) and `events` (customer events with fields like customer_id, timestamp, category). Profile documents will get a `segment` field. Use schemaVersion in documents per data-modeling guidance. | Prompt requires computing per-customer metrics and updating profile docs but does not name collections or document shapes; the data-modeling skill gives patterns but not exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will provide a small idempotent seed script that inserts synthetic `events` and `customers` and creates necessary indexes; sample size small (hundreds of events) and repeatable. | Prompt and skill_md require using the live cluster and sample data but do not supply a concrete seed dataset or license. |
| Queries and indexes | ambiguous | no | "DocumentDB aggregation tool ... computes behavioural metrics (recency, frequency, category affinity)" | documentdb-indexing | Builder will implement aggregation pipelines over the `events` collection (group by customer, compute recency from max timestamp, frequency as count in a window, category affinity as category counts/ratios) and create indexes such as {customer_id:1, timestamp:-1} and {customer_id:1, category:1}. The indexing skill will be followed to choose appropriate index shapes. | Pipeline intent is specified but exact pipeline, filter windows, and indexes are not; the indexing skill will guide index choices. |
| AI components | ambiguous | no | "Python LangChain agent" and "inject segmentation rules into the prompt" | documentdb-vector-search | Builder will use a hosted embedding/chat provider (commonly OpenAI) and a standard embedding model (e.g., text-embedding-3-small or similar) if embeddings are needed; embedding dimension chosen to match any vector index. If the sample does not require semantic vectors, no vector index will be used. | Prompt requires LangChain but does not name chat or embedding models or providers; vector-capable cluster exists but using vectors is optional and must be aligned with the chosen embedding model/dimensions. |
| App surface | ambiguous | no | "agent ... computes ... on demand" | - | Builder will provide a minimal CLI and a small HTTP endpoint (FastAPI) such as POST /segment or GET /segment?customer_id=... which triggers the LangChain agent for a given customer, returning the assigned segment and writing it back. | Prompt doesn't specify CLI vs API vs UI; the builder will pick a simple runnable surface to demonstrate the flow. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | No new cluster will be provisioned by the sample; the sample will use the existing cluster. Infrastructure-as-code for creating the cluster will not be provided unless explicitly requested. | The reference requirements expect infra-as-code for the cluster but the starter prompt and skill_md say a cluster already exists and discourage provisioning for this run. |
| Run and test instructions | missing | no | - | - | README will include the standard sequence: pip install -r requirements.txt, copy .env.example to .env and fill in DOCUMENTDB_URI and any model keys, run seed script, start the app, and run unit tests with pytest. Exact commands and expected outputs will be added by the builder. | skill_md gives runtime context but the prompt doesn't provide explicit commands or success criteria. |
| Definition of done | missing | no | - | - | Builder will treat 'done' as: agent computes metrics on-demand via the tool, assigns a segment based on injected rules, writes the segment back to the customer's profile, and includes a small demo run that shows the write occurring. | No explicit acceptance criteria in prompt; builder will impose pragmatic checks. |
| Constraints and non-goals | missing | no | - | documentdb-high-availability | Builder will avoid provisioning large/expensive resources and will keep dataset small for the sample; production HA/DR and costly indexing decisions are out of scope for the sample. | Prompt doesn't define cost or non-goals; HA guidance is available in skills but not mandated. |
| Repository conventions | ambiguous | no | - | documentdb-local-deployment | Repository will include README, src/ or app/ layout, requirements.txt with pinned versions, .env.example with placeholders, tests/ with unit tests, and scripts/seed.py for idempotent seeding. | skill_md and local-deployment give guidance (e.g., .env.example, seed scripts), but the prompt does not enumerate repository layout or naming conventions. |
