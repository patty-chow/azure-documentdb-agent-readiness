# Documentation and tooling gaps: 08-insurance-pre-auth-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] PHI logging guidance

- **What was missing:** There is no authoritative public DocumentDB page or sample guidance on which fields to redact and how to implement PHI redaction in logs for DocumentDB-based applications. The discovery step returned only prior_knowledge_only notes for PHI redaction.
- **Where the agent looked:** Searched Microsoft docs for 'Azure DocumentDB PHI logging best practices', 'DocumentDB redact logs PHI', and internal agent kit skills; none provided a dedicated PHI/logging guidance page.
- **Effect on this build:** The repository includes only a brief README 'Security & PHI note' but no code or examples demonstrating redaction; builders may accidentally log sensitive fields during debugging.
- **Suggested fix (learn_doc):** A short guidance page titled 'Handling PHI and logging with Azure DocumentDB' that: (1) states which fields are commonly considered PHI (patientId, clinician, clinicalNotes, identifiers), (2) provides example redaction helper functions (redactFields(obj, ['patientId','clinician']) ), (3) shows how to configure logging libraries to omit fields, (4) includes sample code for Node.js apps and a README snippet explaining compliance considerations.

## [high] Orchestrator resume & idempotency pattern

- **What was missing:** No public, agent-discoverable example defining when and how to persist intermediate orchestrator state (reviewResult, draftDocument) for Node + DocumentDB multi-agent flows.
- **Where the agent looked:** Searched agent-kit skills and Microsoft docs for 'orchestrator persisted state resume retries' and 'idempotent orchestrator pattern DocumentDB' with no practical sample found.
- **Effect on this build:** The sample omits persisting intermediate state; a transient failure during the orchestration could cause duplicate submissions or lost progress. The builder chose a simple final-write-only approach, which works for small demos but is a brittle pattern in real deployments.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and short example page 'Orchestrator patterns for DocumentDB samples' that prescribes persisting each step (reviewResult, draftDocument) into the preauth document with timestamps and shows code examples using updateOne with upsert and version checks. Include a templated document shape and minimal retry/resume pseudo-code.

## [high] Default LLM env names and embedding model recommendation

- **What was missing:** There is no single, discoverable product guidance that tells agents which environment-variable names and default model names to use for LLM and embedding models for DocumentDB samples; builder decisions used OPENAI_API_KEY and CHAT_MODEL but EMBEDDING_MODEL was discussed and not consistently implemented.
- **Where the agent looked:** Searched agent-kit skills and README examples; skill docs mention LLM usage patterns but do not prescribe a canonical set of env names for sample repositories.
- **Effect on this build:** The builder implemented OPENAI_API_KEY and CHAT_MODEL but left EMBEDDING_MODEL out of .env.example and code. An agent reusing model-defaults could choose a model/dimension not aligned with a vector index if one were later added.
- **Suggested fix (discoverability):** Add a short product note and sample .env.example template in the agent-kit docs specifying canonical env names: OPENAI_API_KEY, CHAT_MODEL, EMBEDDING_MODEL, EMBEDDING_DIM, and explaining default choices and their dimensions (e.g., text-embedding-3-small => 1536 dims).

## [medium] Optimistic concurrency guidance for samples

- **What was missing:** Public guidance showing a concise pattern for optimistic concurrency (version field or ETag/If-Match) in MongoDB-compatible DocumentDB samples.
- **Where the agent looked:** Searched Microsoft docs for 'DocumentDB optimistic concurrency ETag If-Match' and agent skills; found general concurrency docs but not a small sample pattern for Node.js.
- **Effect on this build:** The sample updates preauth status without version checks; concurrent runs against the same preauth could cause lost updates in more realistic loads.
- **Suggested fix (learn_doc):** A short example titled 'Optimistic concurrency in DocumentDB (Node.js)' showing a versioned document (version integer), a sample updateOne filter that includes the current version, and fallback logic when updates fail due to version mismatch. Include an example using findOneAndUpdate returning pre- and post-values.

## [medium] Side-by-side guidance: text index vs createSearchIndexes

- **What was missing:** While createSearchIndexes and native full-text/hybrid search pages exist, there is no short, discoverable page that tells sample authors which approach to pick for small demo samples vs production (i.e., when to use simple Mongo text index vs DocumentDB createSearchIndexes).
- **Where the agent looked:** DocumentDB full-text search docs and agent-kit indexing skill pages were found but not a one-paragraph 'Which one to choose' note for sample authors.
- **Effect on this build:** Builder chose a simple Mongo text index for simplicity (documented in README) but the product guidance prefers createSearchIndexes for richer search; an agent might choose the suboptimal approach or produce inconsistent samples.
- **Suggested fix (discoverability):** A short decision guide 'Choosing full-text search in DocumentDB samples' that explains: (a) use a Mongo text index only for tiny demos and note limitations; (b) prefer createSearchIndexes for realistic full-text/hybrid search; (c) provide a small code snippet for createSearchIndexes usage in the seed script.

