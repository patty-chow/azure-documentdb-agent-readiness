# 5a. Best practices: prior knowledge against the public record: 11-correspondent-banking-risk-screener

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**42 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 8 | Memory and documentation line up. |
| Found in public sources only | 34 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Require the DocumentDB connection string to be supplied from the DOCUMENTDB_URI environment variable at runtime and provide a .env.example placeholder instead of committing secrets. | authentication_and_secrets | prior_knowledge_confirmed | .env.example / src/db.py / README.md (local_file) | **none** | search: DOCUMENTDB_URI | yes |
| P02 | Create and reuse a single MongoClient instance for the process (module-level client) and use it for all collection access. | connection_handling | prior_knowledge_confirmed | src/db.py (local_file) | **none** | open file: src/db.py | yes |
| P03 | Create simple primary-key/identity indexes for collections (correspondents, sanctions, adverse_media) on startup to support lookups. | indexing | found_in_public_source | src/db.py (local_file) | **none** | open file: src/db.py | yes |
| P04 | For production, create a proper server-side vector index (e.g., HNSW/IVF/DiskANN) on the embedding field rather than relying on client-side similarity. | vector_search | found_in_public_source | README.md / src/db.py (local_file) | **none** | open file: README.md | yes |
| P05 | Make the seed operation idempotent by using upserts (replace_one / upsert=True) so repeated runs do not create duplicates. | provisioning_and_seeding | prior_knowledge_confirmed | scripts/seed.py (local_file) | **none** | open file: scripts/seed.py | yes |
| P06 | Provide a deterministic synthetic-embedding fallback (used for seeding and runtime when OPENAI_API_KEY is not present) so the sample can run without external keys and produce reproducible vectors. | vector_search | prior_knowledge_confirmed | scripts/seed.py / src/agent.py (local_file) | **none** | search: synthetic_embedding in scripts/seed.py and src/agent.py | yes |
| P07 | Exclude or do not return full embeddings in API responses; compute similarity server- or client-side but omit embedding bytes from the public result payload. | data_modeling | prior_knowledge_confirmed | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P08 | Limit the sample to a dedicated database name (sample_banking_11) and avoid touching other databases in the cluster. | authentication_and_secrets | prior_knowledge_confirmed | src/db.py / README.md (local_file) | **none** | search: sample_banking_11 | yes |
| P09 | Include TLS in the example connection string (ssl=true) to suggest encrypted connections in the sample configuration. | connection_handling | found_in_public_source | .env.example (local_file) | **none** | open file: .env.example | yes |
| P10 | When a server-side vector index cannot be created automatically, compute vector similarity client-side (numpy) as a fallback so the sample remains portable across clusters. | vector_search | found_in_public_source | README.md / src/db.py (local_file) | **none** | open file: README.md | yes |
| P11 | Handle failures to create indexes gracefully (catch PyMongoError and warn) instead of crashing the application during startup. | provisioning_and_maintenance | found_in_public_source | src/db.py (local_file) | **none** | open file: src/db.py | yes |
| P12 | Ensure the data-plane account used for seeding and runtime allows writes and the cluster is reachable before attempting seeding or queries. | provisioning_and_monitoring | found_in_public_source | README.md (local_file) | **none** | open file: README.md | yes |
| P13 | If server-side vector indexes are available, prefer them in production; the sample explicitly avoids creating cluster-specific vector indexes so the user can add an appropriate managed index later. | vector_search | found_in_public_source | README.md / src/db.py (local_file) | **none** | open file: README.md | yes |
| P14 | Provide a .env.example with placeholders and explicit instructions not to commit real secrets to source control. | authentication_and_secrets | found_in_public_source | .env.example / README.md (local_file) | **none** | open file: .env.example | yes |
| P15 | Store embeddings as lists of floats in a dedicated 'embedding' field on documents (the sample stores 1536-dim embeddings in an 'embedding' field). | vector_search | found_in_public_source | scripts/seed.py / src/embeddings.py / src/agent.py (local_file) | **none** | search: embedding in repository | yes |
| P16 | Separate responsibilities: compute embeddings in a dedicated module (src/embeddings.py) and call them from the seeding and runtime code so embedding logic is centralized. | code_structure | found_in_public_source | src/embeddings.py / scripts/seed.py / src/agent.py (local_file) | **none** | open file: src/embeddings.py | yes |
| P17 | Provide both seeding and runtime paths that fall back to deterministic embeddings so CI/DEV environments can run without external API keys. | testing | found_in_public_source | scripts/seed.py / src/agent.py (local_file) | **none** | search: OPENAI_API_KEY fallback | yes |
| P18 | When computing runtime similarity in the client, fetch only documents that have an 'embedding' field and project the minimal fields required for scoring. | queries | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P19 | Format and cap returned matches (e.g., top 10) and present only selected metadata (id, title, score, source, date) rather than raw documents. | queries | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P20 | Use a deterministic, testable narrative fallback when an LLM is not available (produce a deterministic plain-language summary based on scores and matches). | testing | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P21 | Document the quickstart steps: install, set environment variables (using .env.example), run seed script, and run the API using uvicorn. | operations | found_in_public_source | README.md (local_file) | **none** | open file: README.md | yes |
| P22 | Do not assume server-side vector index creation will succeed in sample scripts; allow the seed script to continue and report what succeeded. | provisioning_and_seeding | found_in_public_source | README.md / scripts/seed.py / src/db.py (local_file) | **none** | open file: README.md | yes |
| P23 | Store sample data with human-readable dates and metadata in JSON for seeding (the sample uses ISO-like date strings in data/*.json), but the sample does not convert them to ISODate on insert. | data_modeling | found_in_public_source | data/*.json (local_file) | **none** | open files: data/correspondents.json, data/sanctions.json, data/adverse_media.json | yes |
| P24 | Separate seeding and runtime concerns (seed script computes and stores embeddings; runtime recomputes query embedding and searches against stored vectors). | provisioning_and_seeding | found_in_public_source | scripts/seed.py / src/agent.py (local_file) | **none** | open files: scripts/seed.py and src/agent.py | yes |
| P25 | If server-side vector search is not used, perform straightforward client-side re-ranking using cosine similarity over stored embeddings as a simple and portable approach. | vector_search | prior_knowledge_confirmed | README.md / src/agent.py / src/db.py (local_file) | **none** | search: client-side similarity in README.md and src/agent.py | yes |
| P26 | Log warnings and progress during seeding (the seed script prints seeded counts and warns on index creation failures) to help troubleshoot provisioning. | provisioning_and_monitoring | found_in_public_source | scripts/seed.py / src/db.py (local_file) | **none** | open file: scripts/seed.py | yes |
| P27 | Provide example usage for the API endpoint (/review) and examples for calling it with either a correspondent_id or inline profile_text. | operations | found_in_public_source | README.md / src/main.py (local_file) | **none** | open file: README.md | yes |
| P28 | Use a small deterministic test fixture in unit tests (tests/test_agent.py uses small mocked embeddings and documents) to avoid network dependency in CI. | testing | found_in_public_source | tests/test_agent.py (local_file) | **none** | open file: tests/test_agent.py | yes |
| P29 | Centralize the LLM usage behind an optional dependency: use LangChain if available and fall back to deterministic text generation if not. | dependencies | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P30 | When computing cosine similarity client-side, normalize synthetic embeddings (the sample normalizes the synthetic vector) to avoid zero-length vectors and ensure stable similarity scores. | vector_search | found_in_public_source | src/agent.py / scripts/seed.py (local_file) | **none** | search: synthetic_embedding normalization in repository | yes |
| P31 | Do not include the cluster connection string in logs or README; include a clear warning to not commit secrets (sample README and .env.example do this). | authentication_and_secrets | prior_knowledge_confirmed | README.md / .env.example (local_file) | **none** | open file: README.md and .env.example | yes |
| P32 | Do not assume ISODate conversions: the sample stores date strings in data/*.json and does not convert them to BSON ISODate when inserting. | data_modeling | found_in_public_source | data/*.json / scripts/seed.py (local_file) | **none** | open files: data/sanctions.json and data/adverse_media.json | yes |
| P33 | Do not depend on seed-time creation of complex cluster-specific indexes; the sample keeps index creation conservative and lets users add vector indexes manually. | provisioning_and_seeding | found_in_public_source | src/db.py / README.md (local_file) | **none** | open file: src/db.py | yes |
| P34 | When seeding multiple collections, compute embeddings in batches (the seed script computes embeddings for lists of texts where possible). | provisioning_and_seeding | found_in_public_source | scripts/seed.py / src/embeddings.py (local_file) | **none** | open file: scripts/seed.py | yes |
| P35 | For hybrid searches, the sample separates data into collections (sanctions vs adverse_media) and performs separate similarity searches per collection before merging results. | vector_search | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P36 | If an LLM is used, make it optional and controlled by the presence of the OPENAI_API_KEY so the system can run without LLM access in test/dev environments. | dependencies | found_in_public_source | src/agent.py / src/embeddings.py (local_file) | **none** | open file: src/agent.py | yes |
| P37 | When embedding via OpenAI, centralize setting the API key and optionally support an alternative base (OPENAI_API_BASE) for Azure OpenAI endpoints in the embeddings module. | vector_search | found_in_public_source | src/embeddings.py (local_file) | **none** | open file: src/embeddings.py | yes |
| P38 | Use mocked small embeddings and documents in unit tests rather than hitting the live cluster or external embedding APIs to keep tests fast and reliable. | testing | found_in_public_source | tests/test_agent.py (local_file) | **none** | open file: tests/test_agent.py | yes |
| P39 | Provide clear quickstart instructions that note the need for cluster data-plane write permissions to allow seeding to succeed. | operations | found_in_public_source | README.md (local_file) | **none** | open file: README.md | yes |
| P40 | Keep vector dimensionality consistent across seeding and runtime (the sample uses a 1536-dim embedding model and the synthetic generator uses 1536 dims). | vector_search | found_in_public_source | src/embeddings.py / scripts/seed.py / src/agent.py (local_file) | **none** | search: MODEL_NAME = "text-embedding-3-small" and synthetic_embedding dims | yes |
| P41 | When computing cosine similarity, guard against zero-length vectors and return a safe default score (the sample returns 0 when a vector norm is zero). | vector_search | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |
| P42 | Present a capped number of top matches (e.g., top_k per collection and then global top-N) to limit response size and computation. | queries | found_in_public_source | src/agent.py (local_file) | **none** | open file: src/agent.py | yes |

## Searches that returned nothing useful

- Azure DocumentDB TLS validate server certificate
- Azure DocumentDB connectTimeoutMS serverSelectionTimeoutMS socketTimeoutMS guidance
- Azure DocumentDB retryable writes exponential backoff 429 guidance
- Azure DocumentDB RU/s autoscale monitor 429 provisioning best practices
- Azure DocumentDB server-side vector index parameters dimensions metric example
- Azure DocumentDB schema validation embedding dimensionality enforcement
- Azure DocumentDB TTL index guidance for retention-based collections
- Azure DocumentDB backup and restore recommendations mongodump mongorestore

## Notes

All public/practical guidance discovered here comes from the sample repository files (README, .env.example, src/, scripts/, data/, tests/). No external documentation servers were available in this run; where prior beliefs were not present in the repository I recorded them as prior_knowledge_only entries below.

Prior beliefs the discovery step did not classify: K02, K04, K05, K08, K09, K10, K11, K12, K14, K17, K18, K19, K20, K21, K22, K23, K24. See 05a-prior-beliefs.json.

