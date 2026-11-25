# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| operator | 2 |
| skill | 2 |
| model_default | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:18:55+00:00

## D002 (build): I chose Python 3.11 as the language/runtime for the sample app.

- **Instead of:** JavaScript/Node.js; Python 3.10/3.11
- **Because:** Python is the requested language in the sample prompt and the run environment provides Python. It's the common choice for LangChain samples and allows using pymongo and LangChain readily.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Builder will target a current, common Python runtime such as Python 3.10 or 3.11 (virtualenv available per run environment).
- **When:** 2026-11-25T10:19:25+00:00

## D003 (build): I chose OpenAI via LangChain (OPENAI_API_KEY).

- **Instead of:** OpenAI; Azure OpenAI; Anthropic
- **Because:** OpenAI is commonly available and integrates with LangChain; keeping provider choice simple for sample. Code will fall back to a local template if key is missing.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will call an LLM via LangChain (e.g., OpenAI's chat model) and place model credentials in env vars like OPENAI_API_KEY.'
- **When:** 2026-11-25T10:19:42+00:00

## D004 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:22:45+00:00

## D005 (build): I chose Python 3.11 (virtualenv) as the runtime.

- **Instead of:** Node.js; Python 3.11; Python 3.10
- **Because:** Python is the most natural language for LangChain and the run environment provides Python; 3.11 is a current common runtime.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a current, common Python runtime such as Python 3.10 or 3.11 (virtualenv available per run environment).
- **When:** 2026-11-25T10:23:08+00:00

## D006 (build): I chose OpenAI (OPENAI_API_KEY via environment) as the LLM provider with a fallback to a local rule-based commentary when the key is not present.

- **Instead of:** Use Azure OpenAI; Use OpenAI (api.openai.com); Use Anthropic
- **Because:** OpenAI is commonly available in examples and integrates with LangChain; using environment variable keeps secrets out of files. Fallback avoids failing verification when keys are absent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will call an LLM via LangChain (e.g., OpenAI's chat model) and place model credentials in env vars like OPENAI_API_KEY.'
- **When:** 2026-11-25T10:23:11+00:00

## D007 (build): I chose to use the pre-provisioned live Azure DocumentDB cluster via DOCUMENTDB_URI and not provision new resources.

- **Instead of:** Provision new cluster with Bicep/az; Use existing DOCUMENTDB_URI live cluster
- **Because:** The run policy forbids Azure resource changes and a live cluster is already provided; using the provided connection is simplest and allowed.
- **Reason came from:** `skill`
- **Evidence:** skill_md run environment: 'A vector-capable Azure DocumentDB cluster ... Its connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T10:23:21+00:00

## D008 (build): I chose nested capital object with fields capital.cet1 and capital.total to represent capital elements in each position document.

- **Instead of:** Use nested capital fields (capital.cet1); Use flat capital fields (cet1, total_capital)
- **Because:** Nested 'capital' groups capital elements logically and makes it extensible for tier entries; it's a common pattern in financial doc schemas.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'position documents with numeric fields like risk_weighted_assets (rwa), cet1 (CET1 capital), and total_capital (or similar).'
- **When:** 2026-11-25T10:23:23+00:00

## D009 (build): I chose to rely on the default _id index and not create special indexes because the sample aggregation is a full-collection $group summation.

- **Instead of:** Create additional indexes for filters; Rely on default _id index and no extra indexes
- **Because:** A full-collection aggregation will scan the collection; adding indexes would not help the $group unless filtered. Simplicity for sample is preferred.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'no special indexes are strictly required for a full-collection aggregation.'
- **When:** 2026-11-25T10:23:25+00:00

## D010 (build): I chose to use a process-wide singleton MongoClient (singleton pattern) for connections to DocumentDB.

- **Instead of:** Create new MongoClient per call; Use a process-wide singleton MongoClient reused across calls
- **Because:** Prevents connection leaks and follows driver best practices for Azure DocumentDB.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill: 'Reuse `MongoClient` as a process-wide singleton; never create a new client per request.'
- **When:** 2026-11-25T10:23:35+00:00
