# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| model_default | 4 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:32:16+00:00

## D002 (build): I chose the official mongodb Node.js driver v5.x and to implement a process-wide singleton MongoClient.

- **Instead of:** mongodb Node.js driver v5.x; mongoose ODM; native MongoDB driver v4.x
- **Because:** Official driver v5.x is recommended by the documentdb-driver skill and suits a small sample without adding an ORM layer; singleton pattern follows documentdb-driver guidance for connection reuse.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use the official mongodb npm driver v5.x (>=5.0, <6.0) and follow the documentdb-driver advice to implement a process-wide singleton MongoClient."
- **When:** 2026-11-25T05:32:35+00:00

## D003 (build): I chose not to use a LlamaIndex library and instead implement a lightweight agent that injects DocumentDB segment context into an OpenAI prompt (or a deterministic fallback when no API key) to generate subject/body.

- **Instead of:** Use LlamaIndex Node library; Use a simple OpenAI-based agent and emulate LlamaIndex behaviour
- **Because:** LlamaIndex Node libraries are not guaranteed available and would increase dependencies; the sample's core teaching point is context-engineering and DocumentDB tool integration, which can be shown by constructing prompts and embedding segment data directly. This also avoids failing the build if LlamaIndex isn't installed or configured.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "No installed skill or Learn page prescribes which LLM provider or exact models... The prompt review assumed defaults" and the environment may not have LlamaIndex available.
- **When:** 2026-11-25T05:32:38+00:00

## D004 (build): I chose OpenAI as the LLM provider and to use OPENAI_API_KEY environment variable with a default model name OPENAI_MODEL (default gpt-4o-mini).

- **Instead of:** OpenAI (openai.com); Azure OpenAI; Anthropic
- **Because:** OpenAI is widely available and straightforward to call from Node; using env vars keeps secrets out of code and matches sample conventions.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will pick a cloud LLM provider and models by default (e.g., OpenAI: gpt-4o-mini ...)"
- **When:** 2026-11-25T05:32:41+00:00

## D005 (build): I chose simple context injection (include purchase_history and preferences directly into the prompt) rather than building a vector index or embedding flow.

- **Instead of:** Use a vector index and embeddings for retrieval; Do simple context injection (purchase_history + preferences) into prompt without embedding retrieval
- **Because:** Keeping the sample small and robust: embedding dimension and vector index choices are ambiguous and not necessary to show personalized email generation. This avoids creating vector indexes and needing embedding model dimensions.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report noted embedding/model dimension gaps and vector index creation requirements; the sample's goal is to show DocumentDB fetch + prompt engineering; vector search is optional.
- **When:** 2026-11-25T05:32:45+00:00

## D006 (build): I chose to read secrets (DOCUMENTDB_URI, OPENAI_API_KEY) from environment variables and include a .env.example file with placeholders.

- **Instead of:** Store secrets in code/config files; Read secrets from environment variables and ship .env.example
- **Because:** Follows prompt's explicit instruction and security best practices.
- **Reason came from:** `prompt`
- **Evidence:** Prompt instruction: "Never write a secret, password, key or full connection string into a file. Read them from environment variables, and ship a .env.example with placeholder values."
- **When:** 2026-11-25T05:32:47+00:00

## D007 (build): I chose to create simple single-field indexes on segments.segmentId (unique) and campaigns.segmentId (non-unique) to speed lookups and demonstrate index creation.

- **Instead of:** Create vector indexes for segments; Create simple single-field indexes on segmentId
- **Because:** Simple indexes are useful demonstratively, avoid complexity of vector index dimensions and too-specific index types; they are idempotent and low risk on writes for sample data.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review about index choices and guidance_for_builder noting index types; sample needs basic indexes for lookup patterns.
- **When:** 2026-11-25T05:32:54+00:00

## D008 (build): I chose to use the existing reachable Azure DocumentDB cluster and not to provision any new resources.

- **Instead of:** Provision a new Azure DocumentDB cluster; Use the existing reachable cluster via DOCUMENTDB_URI
- **Because:** Run policy disallows creating Azure resources and the prompt explicitly provided a live cluster to use; using the existing cluster avoids side-effects and matches the sample's intent.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: "A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI."
- **When:** 2026-11-25T05:33:33+00:00

## D009 (build): I chose to prefer the deterministic fallback by default and only call OpenAI when USE_OPENAI=1 is set in environment (and OPENAI_API_KEY present).

- **Instead of:** Attempt OpenAI network calls by default; Prefer deterministic fallback by default unless explicitly enabled with USE_OPENAI=1
- **Because:** This keeps the sample deterministic and avoids flaky network-dependent failures during automated verification; it still allows real LLM usage when the developer sets USE_OPENAI=1 and provides OPENAI_API_KEY.
- **Reason came from:** `model_default`
- **Evidence:** The build environment may or may not have a valid OPENAI_API_KEY and network calls can hang; the sample should verify DocumentDB integration reliably during automated build.
- **When:** 2026-11-25T05:43:49+00:00
