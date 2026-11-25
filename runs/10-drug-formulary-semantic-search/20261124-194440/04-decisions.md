# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 2 |
| operator | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:31:46+00:00

## D002 (build): I chose Python 3 with FastAPI (uvicorn) as the web framework.

- **Instead of:** Python 3 (Flask); Python 3 (FastAPI)
- **Because:** FastAPI is lightweight, async-friendly, and integrates well with uvicorn and LlamaIndex; it's suitable for a small sample service.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt_review: 'Use a modern Python 3.x runtime...'; FastAPI is a common choice for small services and supports ASGI/uvicorn as in README assumption.
- **When:** 2026-11-25T08:32:02+00:00

## D003 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); OpenAI text-embedding-3-large (3072?); Hugging Face local model
- **Because:** OpenAI embeddings are widely available, and 1536 is a common dimension size used in examples; this keeps the sample simple and compatible with LlamaIndex.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'assume OpenAI text-embedding-3-small or another commonly used embedding model' and 'many OpenAI embeddings use 1536 dims'.
- **When:** 2026-11-25T08:32:05+00:00

## D004 (build): I chose not to run pytest because pytest is not installed in the environment.

- **Because:** Cannot run tests without pytest; installing more tools is outside sample scope.
- **Reason came from:** `tool_result`
- **Evidence:** Command runner output: "NOT INSTALLED: 'pytest' was not found on PATH."
- **When:** 2026-11-25T08:34:30+00:00
