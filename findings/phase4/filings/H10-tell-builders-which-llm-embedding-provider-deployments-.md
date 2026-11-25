---
id: H10
title: "Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 42
member_drafts:
  - 049-sample-prompts-never-name-the-llm-embedding-provider-model-c.md
open_questions: 3
---

# Tell builders which LLM/embedding provider, deployments, env vars and no-key fallback to use

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR.

## What happens today

This harness asks a coding agent to build 100 Azure DocumentDB gallery samples from starter prompts in `samples/`. About three quarters of those prompts (76 of 101 sample files match a keyword grep for OpenAI, LLM, embedding, LangChain, LlamaIndex, GPT or prompt engineering) need an LLM or an embedding model. Only one names a model (`samples/retail/01-product-catalog-with-vector-search.md`, `text-embedding-ada-002`) and none mention Azure OpenAI. No prompt says which provider to use (public OpenAI, Azure OpenAI or local), which chat or embedding deployment, which env-var names hold credentials, whether real model calls are required, how much LLM concurrency is allowed, or (for LangChain) where agent memory lives.

`loop/run-environment.md`, rendered by `render_env_note` in `loop/run_loop.py` and passed to every run unless `--no-env-note` is given, covers the cluster, `DOCUMENTDB_URI`, the database, Python/Node and `az`. It says nothing about an AI provider, although `run_loop.py` sets `AZURE_OPENAI_ENDPOINT` in the run's environment and `az` is signed in. `prompts/builder.md` asks the builder to log its "embedding or chat model, and dimensions" decision but gives no default, so the choice is always a `model_default`.

The readiness stage flags this every time. Neither the Azure DocumentDB Learn pages nor the Agent Kit skills prescribe an LLM vendor, and they should not; the decision belongs in the prompt and the run environment.

## Why it matters

In one experiment run, the readiness stage raised 49 `information_gap` findings on this topic across **42 of the 100 samples** (recounted from the finding ids; counts come from a single run and may shift on a re-run). Typical gaps: "LLM provider and model selection", "Exact env var names for LLM keys", "Do we require live LLM calls in the end-to-end verification?", "LangChain provider & memory store choice".

With the decision left open, every builder answered differently. Across the 120 run folders with a `04-decisions.md`:

- No run chose Azure OpenAI, the provider the experiment itself runs on. It appears only as a rejected alternative; three logs chose public OpenAI and said users could switch to Azure OpenAI later by changing code or configuration.
- 71 logs reference `OPENAI_API_KEY`, 18 mention `gpt-3.5-turbo`, and at least 5 pin the legacy `openai` 0.x Python SDK.
- 30 logs describe a home-grown stub or mock for when no key is present, each shaped differently and not always documented.
- `.env.example` files use many names for the same setting (`OPENAI_MODEL`, `LLM_MODEL`, `CHAT_MODEL`, `EMBEDDING_DIM`, `EMBEDDING_DIMENSIONS`, ...).
- One builder dropped LangChain entirely rather than pick a provider, so the sample no longer demonstrates what its title promises.

Each of these is a decision the audit has to review, and it drowns the signal the harness exists to measure: how well the agent handles Azure DocumentDB itself (`Microsoft.DocumentDB/mongoClusters`, `az documentdb mongocluster`, `cosmosSearch` vector indexes, vCore tiers, Entra ID auth).

## Proposed change

### 1. `loop/run-environment.md`

Append after the existing bullets (deployment names must match ones that exist in the Azure OpenAI resource the builders will call):

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

### 2. `requirements/retail-semantic-search.md`, section "What a gallery sample also needs"

`loop/draft_requirements.py` copies this section verbatim into all 102 `requirements/*.md` files, so edit it here and then re-sync the others (or regenerate with `--overwrite`). Keep the existing credentials line and add two conditional lines so non-AI samples are not failed:

```markdown
- The connection string and model credentials come from environment variables; none appear in the repository.
- If the sample calls a model: it uses Azure OpenAI through the `AZURE_OPENAI_*` variables listed in `.env.example`, with no public-OpenAI-only code path.
- If the sample calls a model: it runs end to end with a documented deterministic stub when no model credential is present, and the README says so.
```

The same file's first section says "Embeddings are stored as BSON binary vectors." Azure DocumentDB vector indexes cover embeddings stored as number arrays, so that line should be corrected in the same pass (tracked separately). The starter prompt `samples/retail/01-product-catalog-with-vector-search.md` also asks to "store them as BSON binary vectors", which would conflict with the conventions block above; it needs the same correction.

Out of scope for this PR: copying the conventions block into the samples spreadsheet's Starter Prompt column (so `loop/import_samples.py` regenerates `samples/*.md`), and aligning env-var names in the Learn AI-integration tutorials.

## Evidence

- `runs/07-customer-review-sentiment-pipeline/20261125-054042/02-readiness.json` and `04-decisions.md` (D004/D005 pin `openai==0.27.8` and choose public OpenAI)
- `runs/14-loan-origination-workflow-orchestration/20261124-191837/doc-gaps.md` ("LLM provider unspecified"; all agents stubbed)
- `runs/15-prescription-refill-agent/20261124-195253/04-decisions.md` (D006/D007/D011: LangChain replaced; memory backend changed back and forth)
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json` (`OPENAI_API_KEY` vs `AZURE_OPENAI_*` contract missing)
- `runs/11-care-gap-identification-pipeline/20261124-194646/02-readiness.json` (provider affects embedding dimensions and the vector index)

## Open questions

None of the reviewer's SME cautions (retryWrites, change-stream limits, error codes, driver floors, index limits) apply to this change. Maintainer questions:

1. Which chat and embedding deployment names should the defaults use, and should builders call the same Azure OpenAI resource as the pipeline? If so, a separate deployment or a low `LLM_CONCURRENCY` default would keep sample traffic from consuming the pipeline's tokens-per-minute quota, which `run_loop.py` already rotates endpoints to work around.
2. Should public OpenAI be forbidden outright, or allowed when a prompt names it (as proposed)?
3. Should the deterministic-stub fallback be the default for unattended runs, so builds never make live model calls unless asked?

## Source drafts

- 049-sample-prompts-never-name-the-llm-embedding-provider-model-c.md
