---
title: "Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use (loop/run-environment.md + requirements)"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 42
findings: 49
bucket: learn-information_gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use

## What happens today

About three quarters of the starter prompts in `samples/` (76 of the 101 sample files match a keyword grep for OpenAI, LLM, embedding, LangChain, LlamaIndex, GPT or prompt engineering) ask for an LLM or an embedding model ("calls OpenAI to classify sentiment", "LangChain multi-agent", "LlamaIndex RAG chatbot", "use prompt engineering to extract fields"). Exactly one names a model (`samples/retail/01-product-catalog-with-vector-search.md`, `text-embedding-ada-002`), and none mention Azure OpenAI. None name the provider (public OpenAI vs Azure OpenAI vs local), the chat or embedding deployment, the env-var names for credentials, whether real API calls are required, an LLM concurrency bound, or (for LangChain) which memory backend to use.

`loop/run-environment.md` (rendered by `render_env_note` in `loop/run_loop.py` and passed to every run unless `--no-env-note` is given) tells the builder about the cluster, `DOCUMENTDB_URI`, the database, Python/Node and `az`, but says nothing about an AI provider, even though `run_loop.py` sets `AZURE_OPENAI_ENDPOINT` in the run's environment and `az` is signed in. `prompts/builder.md` asks the builder to log the "embedding or chat model, and dimensions" decision but gives no default, so it is always a `model_default`.

The readiness stage flags this every time: 49 `information_gap` findings across 42 distinct samples (e.g. "LLM provider and model selection", "Exact env var names for LLM keys", "Do we require live LLM calls in the end-to-end verification?", "LangChain provider & memory store choice"). The agents correctly observed that neither the Azure DocumentDB Learn pages nor the Agent Kit skills prescribe an LLM vendor, and they should not; the decision is missing from the prompt and the run environment.

## Why it matters

Because the decision is left open, every builder answers it differently. Across the 120 run folders with a `04-decisions.md`:

- No run chose Azure OpenAI, the provider the experiment itself runs on and the one an Azure gallery sample would be expected to use. Azure OpenAI appears only as a rejected alternative; three logs (retail-07, fintech-08, retail-14) explicitly chose public OpenAI and said users "can swap in Azure OpenAI" later.
- 71 logs reference `OPENAI_API_KEY`; 18 mention `gpt-3.5-turbo`; at least 5 pin the legacy `openai` 0.x SDK (e.g. `openai==0.27.8` in `runs/07-customer-review-sentiment-pipeline/20261125-054042/04-decisions.md` D004), which no current sample should ship.
- 30 logs describe a home-grown stub, mock or deterministic fallback for when no key is present; its shape and whether the README documents it vary per run.
- `.env.example` files use many different names for the same settings (`OPENAI_MODEL`, `LLM_MODEL`, `CHAT_MODEL`, `MODEL_NAME`, `EMBEDDING_MODEL`, `EMBED_MODEL`, `EMBEDDING_DIM`, `EMBEDDING_DIMENSIONS`, ...).
- One builder dropped LangChain entirely rather than pick a provider (`runs/15-prescription-refill-agent/20261124-195253/04-decisions.md` D007), so the sample no longer demonstrates what its title promises.

Each of these is a `model_default` decision the audit has to review, and it drowns the signal the readiness stage is meant to give: how well the agent handles Azure DocumentDB (resource type `Microsoft.DocumentDB/mongoClusters`, the `az documentdb mongocluster` CLI group, the connection string, `cosmosSearch` vector indexes, vCore tiers, Entra ID auth). Removing one recurring non-DocumentDB decision from roughly 76 prompts is the cheapest way to sharpen that signal.

## Proposed change

### 1. `loop/run-environment.md`

Append this section after the existing bullets. Wording is a proposal; the deployment names must be ones that exist in the Azure OpenAI resource the builders will call. If that is the same resource the pipeline itself uses, consider a separate deployment (or a low default `LLM_CONCURRENCY`) so sample traffic does not eat the pipeline's own tokens-per-minute quota, which `run_loop.py` already rotates endpoints to work around.

```markdown
## AI provider conventions (apply only when the sample calls an LLM or embedding model)

- Provider: **Azure OpenAI**. Do not use the public OpenAI endpoint, Anthropic, Hugging Face or a local model unless the prompt names one.
- Read these environment variables and list every one of them in `.env.example` with a placeholder:
  - `AZURE_OPENAI_ENDPOINT` (already set in this environment)
  - `AZURE_OPENAI_API_KEY` (optional; when it is empty, authenticate with `DefaultAzureCredential` / `az login`, token scope `https://cognitiveservices.azure.com/.default`)
  - `AZURE_OPENAI_API_VERSION` (default `2024-10-21`)
  - `AZURE_OPENAI_CHAT_DEPLOYMENT` (default `<chat-deployment>`)
  - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (default `text-embedding-3-small`)
  - `EMBEDDING_DIMENSIONS` (default `1536`; create the `cosmosSearch` vector index with this value and store embeddings as a plain array of numbers, not BSON binary, which is not indexed)
- SDKs: `openai>=1` (`AzureOpenAI` / `AsyncAzureOpenAI`) in Python, `openai` v4 or later (`AzureOpenAI`) in Node; with LangChain use `langchain-openai` (`AzureChatOpenAI`, `AzureOpenAIEmbeddings`), with LlamaIndex `llama-index-llms-azure-openai` and `llama-index-embeddings-azure-openai`. Do not pin `openai<1` in Python.
- Bound LLM concurrency (`asyncio.Semaphore` / `p-limit`, default 4, configurable via `LLM_CONCURRENCY`) and retry 429 and 5xx responses with exponential backoff.
- LangChain agent memory: store chat history in an Azure DocumentDB collection (for example `MongoDBChatMessageHistory` from `langchain-mongodb`, or an equivalent collection-backed store), not only in process memory.
- Structured outputs: ask the model for JSON and validate it (Pydantic / zod) before writing to the database.
- **Fallback:** if neither `AZURE_OPENAI_API_KEY` nor an Entra token is available at run time, the sample must still run end to end using a deterministic stub for the model calls, and the README and the build report must say which mode was used. A missing key is not a build failure.
```

### 2. Requirements: "What a gallery sample also needs"

This section is copied verbatim into all 102 `requirements/*.md` files from `requirements/retail-semantic-search.md` by `loop/draft_requirements.py` (marker `## What a gallery sample also needs`). Edit it in `requirements/retail-semantic-search.md` and re-sync the other files (or regenerate with `--overwrite`). Keep the existing credentials line and add two lines that apply only to samples that call a model, so the auditor does not fail non-AI samples:

```markdown
- The connection string and model credentials come from environment variables; none appear in the repository.
- If the sample calls a model: it uses Azure OpenAI through the `AZURE_OPENAI_*` variables listed in `.env.example`, with no public-OpenAI-only code path.
- If the sample calls a model: it runs end to end with a documented deterministic stub when no model credential is present, and the README says so.
```

While editing that file, note that its first section currently says "Embeddings are stored as BSON binary vectors." Azure DocumentDB vector indexes only index embeddings stored as arrays of numbers, so that line should be corrected in the same pass (tracked separately).

### 3. Follow-ups outside this repo (not in this PR)

- **Samples spreadsheet:** paste the same conventions block into the Starter Prompt column for the AI-flavoured samples so gallery builders who never see this harness get it too; `loop/import_samples.py` then regenerates `samples/*.md`.
- **Learn docs:** the Azure DocumentDB AI-integration tutorials (LangChain, LlamaIndex, Semantic Kernel, vector search quickstarts under https://learn.microsoft.com/en-us/azure/documentdb/) could use the same `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_*_DEPLOYMENT` names so prompts, skills and docs agree. This is a consistency nicety, not a docs defect.

## Evidence

- `runs/07-customer-review-sentiment-pipeline/20261125-054042/02-readiness.json`: three gaps (provider/env vars, model and response schema, concurrency); `04-decisions.md` D004/D005 pin `openai==0.27.8` and choose public OpenAI with `OPENAI_API_KEY`, with later decisions on gpt-3.5-turbo, a semaphore and an ad-hoc mock mode.
- `runs/14-loan-origination-workflow-orchestration/20261124-191837/doc-gaps.md`: "Model-default decision: LLM provider unspecified"; the builder stubbed all agents and the audit asked for a rule on stub vs real calls.
- `runs/15-prescription-refill-agent/20261124-195253/02-readiness.json` and `04-decisions.md` D006/D007/D011: no LangChain provider or memory backend named; the builder replaced LangChain with a rule-based agent and went back and forth between in-process and collection-backed memory.
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json`: the gap lists the missing contract, `OPENAI_API_KEY` vs `AZURE_OPENAI_ENDPOINT` + key + deployment name.
- `runs/11-care-gap-identification-pipeline/20261124-194646/02-readiness.json`: two gaps, provider/model (affects embedding dimensions and the vector index) and env-var names for `.env.example`.

## Verification

### 1. Already covered? confirmed (not there)

- `loop/run-environment.md` (the full file) covers the cluster, `DOCUMENTDB_URI`, the database name, the optional MCP line, Python/Node/Docker and `az`; it has no AI-provider, model, env-var or fallback guidance.
- `prompts/builder.md` only asks the builder to log "embedding or chat model, and dimensions" as a decision; no default is given.
- `requirements/retail-semantic-search.md` (source of the shared section in all 102 requirements files) has only "The connection string and model credentials come from environment variables" and "The vector index dimensions match the embedding model's output"; no provider or fallback rule.
- `samples/**/*.md`: no file mentions Azure OpenAI; one names a model (`text-embedding-ada-002`, retail-01).
- For completeness, neither `documentdb-agent-kit/skills` nor `documentdb-agent-kit/knowledge-base` contains any `AZURE_OPENAI_*` variable names, which matches the agents' observation that the kit does not prescribe an LLM vendor (and should not).

### 2. Premise true? confirmed (numbers corrected)

- Core premise verified: prompts and run environment never name the provider; across 120 `04-decisions.md` files no run chose Azure OpenAI (it appears only in "Instead of" alternatives; 3 "Because" lines mention swapping to it later).
- The draft's counts were not reproducible as stated and were replaced with ones measured directly: 76 of 101 sample files are AI-flavoured by keyword grep (draft said 81 of 100); 71 decision logs reference `OPENAI_API_KEY` (draft said 65 chose it); 18 mention gpt-3.5-turbo (matches); at least 5 pin `openai` 0.x (draft said 14; my pattern is narrower); 30 describe a stub/mock (draft said 53). The unverified "22 different variable names" count was replaced with examples.
- `run_loop.py` sets `env["AZURE_OPENAI_ENDPOINT"]` for each run when `FACTORY_OPENAI_ENDPOINTS` is set (otherwise the pipeline's own value is inherited); `render_env_note` is used unless `--no-env-note`. The draft's "rendered into every run" was qualified.
- The draft said `loop/draft_requirements.py` is where to add requirement lines; corrected: that script copies the section verbatim from `requirements/retail-semantic-search.md`, so that file is the source to edit.
- Technical content checked against SDK knowledge: `AzureOpenAI`/`AsyncAzureOpenAI` exist in `openai>=1`; Node `openai` v4+ exposes `AzureOpenAI` (draft's `openai@^4` loosened to "v4 or later"); `2024-10-21` is a GA Azure OpenAI data-plane API version; Entra token scope `https://cognitiveservices.azure.com/.default` is correct; `AzureChatOpenAI`/`AzureOpenAIEmbeddings` are in `langchain-openai`; LlamaIndex Azure packages named correctly; `MongoDBChatMessageHistory` lives in `langchain-mongodb`; `text-embedding-3-small` defaults to 1536 dimensions. Added the Azure DocumentDB fact that vectors must be stored as number arrays (BSON binary vectors are not indexed). Requirement lines were made conditional so non-AI samples are not failed.

### 3. Maintainer skeptic: confirmed

The target is the harness repo itself (`abinav2307/azure-documentdb-agent-readiness`), the change names two concrete files and gives exact text, and it removes a recurring non-DocumentDB `model_default` that the harness's own readiness and audit stages keep flagging. It is not generic hygiene: the stated goal is to keep the readiness signal about Azure DocumentDB. I would accept it with the edits applied (conditional requirement lines, edit the requirements source file, quota caveat). The spreadsheet and Learn follow-ups are correctly marked out of scope for this PR.

## Finding ids

- F0084
- F0225
- F0328
- F0396
- F0433
- F0535
- F0567
- F0706
- F0861
- F0894
- F0952
- F0981
- F1011
- F1050
- F1051
- F1052
- F1114
- F1173
- F1234
- F1272
- F1308
- F1347
- F1381
- F1412
- F1442
- F1534
- F1601
- F1729
- F1764
- F1766
- F1805
- F1838
- F1929
- F1961
- F1992
- F2094
- F2162
- F2198
- F2256
- F2299
- F2336
- F2434
- F2437
- F2528
- F2566
- F2603
- F2722
- F2852
- F3022
