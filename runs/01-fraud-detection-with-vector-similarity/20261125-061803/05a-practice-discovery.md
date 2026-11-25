# 5a. Best practices: prior knowledge against the public record: 01-fraud-detection-with-vector-similarity

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**22 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 10 | Memory and documentation line up. |
| Found in public sources only | 12 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string only from an environment variable (DOCUMENTDB_URI) at runtime and provide a .env.example placeholder rather than committing credentials. | connection & secrets | prior_knowledge_confirmed | README.md / .env.example (local_file) | **none** | .env.example | yes |
| P02 | Use the explicit database name sample_fintech_01 for the app's data rather than relying on defaults or other databases. | provisioning & organization | prior_knowledge_confirmed | seed_data.py / README.md (local_file) | **none** | seed_data.py | yes |
| P03 | Attempt to create a server-side vector index but handle failure gracefully and fall back to client-side similarity search if the cluster does not support the vector index API. | vector search & fallbacks | prior_knowledge_confirmed | README.md / seed_data.py / src/agent.py (local_file) | **none** | README.md | yes |
| P04 | Create the application's collection if it does not exist (create_collection) before seeding data. | provisioning & organization | found_in_public_source | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P05 | Model pattern documents with a stable unique id (pattern_id), a vector field stored as a numeric array (embedding), and metadata fields used for scoring (e.g., severity). | data modeling | prior_knowledge_confirmed | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P06 | Provide a deterministic mock embedding fallback when a real embedding service (OpenAI) is not configured so the demo remains runnable. | embeddings & dev ergonomics | found_in_public_source | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P07 | Limit returned fields in queries (use projection) to only the fields needed for scoring/explanation to avoid transferring large vectors unnecessarily. | queries & performance | prior_knowledge_confirmed | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P08 | Implement client-side cosine similarity and return a small top_k set of matches when server-side vector search is not available. | vector search & fallbacks | found_in_public_source | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P09 | Use bulk insert (insert_many) for seeding multiple pattern documents and clear prior sample docs with a delete_many pattern before re-inserting to keep the seed idempotent. | ingest & seeding | prior_knowledge_confirmed | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P10 | Reuse a single MongoClient instance for the running application (instantiate once and share) rather than creating many short-lived clients. | connection | found_in_public_source | src/app.py / src/agent.py (local_file) | **none** | src/app.py | yes |
| P11 | Attempt server-side vector index creation as a best-effort (create_index) but catch and report failures rather than aborting the seed process. | vector indexing | found_in_public_source | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P12 | Normalize a computed fraud risk score to a fixed 0–100 scale and derive textual explanations from the top N matching documents and their metadata rather than raw distances alone. | scoring & explainability | prior_knowledge_confirmed | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P13 | Enforce a sensible candidate-size limit for searches (e.g., pipeline $limit or top_k) to bound resource usage during vector search. | performance & safety | prior_knowledge_confirmed | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P14 | Prefer server-side ANN/vector indexes for production when supported and fall back to client-side brute-force for small datasets or demos. | vector search & provisioning | prior_knowledge_confirmed | README.md / seed_data.py (local_file) | **none** | README.md | yes |
| P15 | Use insert_many as a bulk write when ingesting multiple seed/training documents to reduce round trips. | ingest & performance | prior_knowledge_confirmed | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P16 | Provide a lightweight health endpoint (GET /health) for basic service readiness checks. | operational | found_in_public_source | src/app.py (local_file) | **none** | src/app.py | yes |
| P17 | Do not commit secrets into the repository or write connection strings into logs or README files; keep secrets in environment variables or external config. | security | found_in_public_source | README.md (local_file) | **none** | README.md | yes |
| P18 | Implement deterministic seeding for examples (deterministic_embedding) so sample data and embeddings are reproducible for tests and demos. | testing & reproducibility | found_in_public_source | seed_data.py (local_file) | **none** | seed_data.py | yes |
| P19 | Store vectors as dense numeric arrays under a dedicated field name (this sample uses 'embedding') so application code can locate and compare them consistently. | data modeling & validation | found_in_public_source | seed_data.py / src/agent.py (local_file) | **none** | seed_data.py | yes |
| P20 | When attempting server-side search features, treat operators (e.g., $search with vector semantics) as best-effort placeholders and catch exceptions because cluster syntax/support varies. | compatibility & resilience | found_in_public_source | src/agent.py / seed_data.py (local_file) | **none** | src/agent.py | yes |
| P21 | When scoring, include matched document metadata (pattern_id, severity, description) in the explanation items returned to callers for clarity. | scoring & explainability | found_in_public_source | src/agent.py (local_file) | **none** | src/agent.py | yes |
| P22 | Catch and continue on index-creation errors during seeding so the demo remains usable even if the cluster does not support the attempted index options. | provisioning & compatibility | found_in_public_source | seed_data.py (local_file) | **none** | seed_data.py | yes |

## Searches that returned nothing useful

- Azure DocumentDB vector index best practices
- Azure DocumentDB vector index nlist efConstruction M parameter guidance
- Azure DocumentDB managed identity MongoDB compatibility rotate keys
- Azure DocumentDB TLS verify server certificate connection string ssl=true
- Azure DocumentDB connection pooling maxPoolSize minPoolSize recommendations
- Azure DocumentDB per-collection throughput / resource controls guidance
- Azure DocumentDB dimension validation for vector fields

## Notes

No external documentation search was available in this run (documentation_search_available=false). All discovered guidance comes from the workspace files (README.md, seed_data.py, src/agent.py, src/app.py, .env.example). For prior beliefs where the workspace contained no supporting or contradicting evidence I recorded the attempted developer-style search queries in how_found and set basis to prior_knowledge_only.

Prior beliefs the discovery step did not classify: K02, K03, K04, K05, K08, K10, K11, K14, K17, K19, K20, K22. See 05a-prior-beliefs.json.

