# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:53:32+00:00

## D002 (build): I chose Python 3.13 (use the system `python` runtime available).

- **Instead of:** Python 3.10; Python 3.13
- **Because:** The run environment already has Python 3.13, so using it avoids extra compatibility work and matches the available interpreter.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "Python 3.13.13 on PATH; `python` and `pip` resolve to a virtual environment"
- **When:** 2026-11-25T05:54:05+00:00

## D003 (build): I chose FastAPI for the minimal HTTP API.

- **Instead of:** Flask; FastAPI
- **Because:** FastAPI provides async endpoints, built-in validation, and easy local testing with uvicorn; it's a good match for a small RAG API.
- **Reason came from:** `model_default`
- **Evidence:** model_default: FastAPI is a modern async framework suitable for small APIs and samples.
- **When:** 2026-11-25T05:54:08+00:00

## D004 (build): I chose pymongo 4.x (pymongo==4.6.0) as the MongoDB driver version.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** pymongo 4.x is current and compatible with MongoDB/DocumentDB 7.0 and supports the driver patterns recommended by the documentdb-driver skill.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-driver skill references using the MongoDB driver and a singleton MongoClient; pymongo 4.x supports MongoDB 7.0 wire protocol.
- **When:** 2026-11-25T05:54:10+00:00

## D005 (build): I chose OpenAI embeddings (configurable via OPENAI_API_KEY and EMBEDDING_MODEL).

- **Instead of:** OpenAI embeddings; Azure OpenAI embeddings; local embeddings (sentence-transformers)
- **Because:** OpenAI embeddings are widely available, easy to use for a sample, and integrate with llama-index examples; the sample will fall back to synthetic vectors if no key is present.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information_gaps notes the embedding model was unspecified; sample environment supports external providers and OpenAI is a common default.
- **When:** 2026-11-25T05:54:13+00:00

## D006 (build): I chose text-embedding-3-small with EMBEDDING_DIM=1536 as the default embedding model/dimension.

- **Instead of:** text-embedding-3-small (1536); text-embedding-3-large (3072); other
- **Because:** 1536 is a common embedding size (matches many OpenAI embeddings) and is a reasonable default for a small demo; the dimension is configurable via EMBEDDING_DIM environment variable to let users override.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: "Embedding model and dimension not specified" and model_default choice for samples often uses 1536-dim embeddings.
- **When:** 2026-11-25T05:54:16+00:00

## D007 (build): I chose OpenAI chat model 'gpt-3.5-turbo' as the default for generating answers (configurable via OPENAI_CHAT_MODEL).

- **Instead of:** gpt-4o-mini; gpt-4o; gpt-3.5-turbo
- **Because:** gpt-3.5-turbo is widely accessible, economical for a sample, and works with the intended prompt/answer flow; users can override via environment variable.
- **Reason came from:** `model_default`
- **Evidence:** information_gaps: LLM choice unspecified; gpt-3.5-turbo is broadly available and inexpensive for samples.
- **When:** 2026-11-25T05:54:19+00:00
