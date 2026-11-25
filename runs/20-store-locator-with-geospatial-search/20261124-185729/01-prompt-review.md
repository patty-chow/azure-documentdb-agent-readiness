# 1. Prompt review: 20-store-locator-with-geospatial-search

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Node.js + Mongoose service with GeoJSON Points, a 2dsphere index, and a /nearby endpoint using $geoNear. Run-environment guidance (Node 24, existing cluster, DOCUMENTDB_URI, .env.example) fills many operational gaps. Some important implementation details (radius units, request parameter format, exact driver/Mongoose versions, seed/data size, README/tests) are unspecified and will be chosen by the builder by reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, App surface, Provisioning and deployment |
| Covered by a skill | 2: Data model, Queries and indexes |
| Ambiguous: builder will guess | 3: Workflow type, Driver and version, Constraints and non-goals |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- Vector index dimensions match an embedding model's output — neither the starter prompt nor the skills lead the builder to create or document vector indexes for this sample (the prompt doesn't request vector features).
- Vector index parameters chosen for sample data and README guidance for scaling them — not implied by the prompt; skills note vector options but the sample doesn't include vector search.
- /search endpoint behaviors (error for empty query, embedding-call failure handling) and similarity score in results — the prompt doesn't request any /search endpoint or embeddings; these are outside the requested scope.
- Dependencies pinned in requirements.txt — the reference expected a pinned requirements.txt (Python-style). The project is Node.js; the prompt doesn't require exact dependency pinning (package-lock or pnpm-lock may be used), so the specific 'requirements.txt' expectation is at risk.
- Unit tests that run without a live cluster — prompt doesn't ask for tests; none are mandated and installed skills provide guidance but won't create such tests by default.
- README that covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't ask for a README; while best-practice skills recommend documentation, it's not required by the prompt and may be omitted.
- Enforcing the use of the exact product name 'Azure DocumentDB' throughout the sample — the prompt does not mandate naming conventions and the builder may use other naming (e.g., 'DocumentDB' or 'Cosmos DB') unless explicitly instructed.

## Questions for the prompt author

- What units should the radius parameter use (meters, kilometers, miles)? This affects the value passed to $geoNear's maxDistance and how the response distance is interpreted.
- Should the /nearby endpoint accept parameters as query string parameters (e.g., ?lat=..&lon=..&radius=..) or as a JSON body? The prompt allows either; choose one for the sample API.
- Do you want a seed script and sample dataset included in the repo (idempotent), or should the sample only include model/schema and the endpoint with no seeded data?
- Should the sample include tests (unit or integration) that run without a live cluster (i.e., mocked DB), or are live-cluster verification steps sufficient?
- Do you require explicit version pinning for dependencies (exact versions in package.json / shrinkwrap), and if so, which versions of Mongoose and Node driver should be used?

## Contradictions and missing references

- "Using the DocumentDB skill" is requested but there is no single installed skill named exactly 'DocumentDB'; instead many documentdb-* skills exist (documentdb-indexing, documentdb-connection, etc.).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose service that stores store locations as GeoJSON Point documents... Expose a /nearby endpoint ... returns stores sorted by distance with opening hours and stock availability." | - | - | Business problem and demonstration are explicit. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" (generic) | - | Assume a single-agent build process that uses the installed documentdb-* skills; no specific agent framework is required. | The prompt references "the DocumentDB skill" generically; there is no single installed skill with that exact name. |
| Language and runtime | specified | no | "Node.js Mongoose service"; run environment (skill.md) specifies Node.js 24 | - | - | Node.js + Mongoose is explicit; skill.md documents Node.js 24 available on the build machine. |
| Driver and version | ambiguous | no | "Mongoose" (no version) | documentdb-driver | Builder will pick a recent Mongoose compatible with Node 24 (e.g., latest stable Mongoose 7.x) and use the driver versions bundled with it; the MongoDB Node driver will be whatever Mongoose depends on. | Prompt specifies Mongoose but gives no version. documentdb-driver covers singleton and best practices, not version pinning. |
| Target service and tier | specified | no | References 'DocumentDB'; run environment skill.md: a reachable M30 cluster (MongoDB 7.0 wire protocol) is present and must be used. | - | - | Skill.md supplies the concrete target cluster and tier (M30) and instructs to use that cluster rather than provisioning a new one. |
| Authentication and secrets | specified | no | - | - | - | skill.md explicitly requires reading the connection string from DOCUMENTDB_URI and never writing secrets into source or logs; .env.example placeholder should be used. |
| Data model | covered_by_skill | no | "stores store locations as GeoJSON Point documents" | documentdb-indexing | Builder will implement schema with GeoJSON Point { type: 'Point', coordinates: [longitude, latitude] } — i.e., GeoJSON coordinate order [lon, lat], as documented in the index guidance. | Prompt requires GeoJSON Points; documentdb-indexing explicitly documents GeoJSON and the required [longitude, latitude] ordering. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will create a small synthetic seed set (e.g., ~10 stores with coordinates, opening hours, and stock) and a seed script; size/license not specified. | Prompt doesn't say what sample data to use, its size, source, or license. local-deployment skill gives guidance on seed scripts but no concrete dataset is specified. |
| Queries and indexes | covered_by_skill | no | "2dsphere index" and "runs a $geoNear aggregation" | documentdb-indexing | Builder will create a 2dsphere index on the location field and implement a $geoNear aggregation with distanceField and maxDistance (maxDistance units to be decided). | Prompt requires $geoNear and a 2dsphere index; documentdb-indexing documents GeoJSON and 2dsphere usage. |
| AI components | not_applicable | no | - | - | - | No embeddings, vectors, or LLM calls are requested by the prompt. |
| App surface | specified | no | "Expose a /nearby endpoint that accepts a latitude, longitude, and radius... returns stores sorted by distance with opening hours and stock availability." | - | Builder may implement the API as an HTTP JSON API (Express) and accept parameters as query params or JSON body; the prompt left that choice open. | Route and required inputs/outputs are clearly stated; parameter-passing method is left flexible. |
| Provisioning and deployment | specified | no | - | documentdb-azure-deployment | Do not provision a new cluster; use the existing cluster described in skill.md. If provisioning were needed, documentdb-azure-deployment exists to do it, but the run environment forbids creating another cluster. | Skill.md explicitly instructs to use the existing reachable cluster and not to provision another one for the sample. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Builder will add typical npm scripts (start, seed, lint, test) and README run instructions (npm install, npm run seed, npm start); exact commands and tests are not specified. | Prompt doesn't supply explicit run/test commands or expected outputs. The build environment (skill.md) gives verification guidance but no explicit command list. |
| Definition of done | missing | no | - | - | Builder will treat successful execution of /nearby against seeded data with correct sorting and required fields returned as the acceptance criteria. | No explicit acceptance criteria (number of results, pagination, performance targets) provided. |
| Constraints and non-goals | ambiguous | no | "Do not provision another cluster unless allowed" (skill.md) | documentdb-local-deployment | Assume cost/infra constraints: use the existing cluster only; avoid provisioning new resources. No other cost or compliance constraints are specified. | Some constraints (use existing cluster) are in skill.md, but broader constraints (cost caps, allowed regions) are not provided. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Builder will use a conventional Node layout (package.json, src/, routes/, models/), include .env.example and a README, but precise conventions (tests layout, CI, dependency pinning format) are not specified. | Prompt doesn't mandate folder layout, README contents, or CI; skill.md recommends .env.example and seed/index scripts but leaves repo conventions to the builder. |
