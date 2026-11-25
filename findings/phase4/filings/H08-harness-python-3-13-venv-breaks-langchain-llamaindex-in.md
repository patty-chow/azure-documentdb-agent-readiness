---
id: H08
title: "Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs and the audit charges it to the sample"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P2
sample_count: 8
member_drafts:
  - 117-build-environment-dependency-failures-langchain-llama-index-.md
open_questions: 2
---

# Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs and the audit charges it to the sample

> This repository belongs to a colleague (abinav2307); coordinate with them before filing.

## What happens today

`loop/run_loop.py` builds each run's virtual environment with `PYTHON = sys.executable` (line 56; `make_venv` at lines 212-215). On the experiment host that interpreter is Python 3.13, and several framework installs fail under it:

- `pip install langchain` resolved to an older pydantic-core pin with no prebuilt cp313 wheel, so pip tried a Rust source build, which failed. The builder dropped LangChain (`05-branch-performance-analytics`, decision D008). Current pydantic-core releases do ship cp313 wheels; this is an old pin meeting a new interpreter.
- The pinned `llama-index==0.9.2` / `0.10.0` dependency chains did not install under 3.13. The builder replaced LlamaIndex with direct OpenAI calls plus a deterministic fallback embedder and described LlamaIndex as optional (`10-support-ticket-rag-assistant` D018; `20-provider-directory-semantic-search` README and `app/seed.py`).
- Pydantic v1 (`pydantic==1.10.12`, `fastapi==0.95.2`) cannot be imported under 3.13 (`ForwardRef._evaluate() missing 1 required keyword-only argument`), so the offline unit tests never ran (`19-option-chain-data-store`).
- `mongomock==4.2.0` failed to install and the pin was loosened to `>=4.2.0` (`16-multi-touch-attribution-model`).

A second, model-side cause compounds this: the builder model targets LangChain's pre-0.1 API. Python used `from langchain.agents import initialize_agent, AgentType` (`14-dynamic-pricing-engine`). Node used `require('langchain/chat_models/openai')` and `require('langchain/schema')`, which fail with `ERR_PACKAGE_PATH_NOT_EXPORTED` because those entrypoints were removed (`18-returns-refund-workflow-orchestration`), and `langchain@^0.0.275`, which fails with npm `ETARGET` (`18-chargeback-dispute-multi-agent` D027). In every case the builder swapped the framework for the plain OpenAI SDK.

The auditor then graded these requirements `partly_met`/`not_met` with `cause=tool_unavailable`, the closest value in `factory/models.py` `RequirementResult.cause`. `loop/findings.py` line 171 routes every non-`skill_silent` cause to the MCP server:

```python
"agent-kit" if r["cause"] == "skill_silent" else "documentdb-mcp",
```

So 13 findings about pip/npm packages were attributed to the DocumentDB MCP server, although none involves DocumentDB or MCP.

## Why it matters

- 8 of the 100 samples lost a framework the prompt explicitly required (13 requirement findings). Counts are from one experiment run and should be re-checked after the fix.
- Those samples now teach "use the OpenAI SDK; LangChain/LlamaIndex are optional", which contradicts the prompt, and one ships a fake embedder as the default path.
- The misrouted findings inflate the MCP-server bucket and debit the agent kit and MCP server in the requirement-met totals (`factory/pipeline.py`, `factory/aggregate.py`) for a harness problem.

## Proposed change

1. **`loop/run_loop.py`**: add `--python PATH` (default `shutil.which("python3.12") or shutil.which("python3.11")`, error if neither exists; python3.12 is present on the host) and use it in `make_venv` instead of `sys.executable`. Keep `sys.executable` for launching `main.py`. Write the resolved version into the rendered `loop/run-environment.md` ("`python` is CPython 3.12.x").
2. **Pre-warm the venv** in `make_venv` from a new `loop/known-good-pins.txt` (`pip install -q -r`): `pydantic>=2.7`, `fastapi`, `langchain>=0.3`, `langchain-openai`, `langchain-azure-cosmosdb` (the current home of the Azure DocumentDB vector store, class `AzureDocumentDBVectorSearch`; `langchain-azure-ai`'s `AzureCosmosDBMongoVCoreVectorSearch` is a deprecation shim since langchain-ai/langchain-azure PR #870, and `langchain-azure-cosmosdb` 1.0.1 pulls `azure-cosmos`, `langgraph` and `langgraph-checkpoint` as hard dependencies), `llama-index>=0.13,<0.15`, `llama-index-vector-stores-azurecosmosmongo==0.9.0` (the current release; it requires `llama-index-core>=0.13,<0.15` and `pymongo>=4.6.1,<5`, so the `llama-index==0.9.2` / `0.10.0` pins the builders chose cannot be installed alongside it, and the explicit range above replaces the earlier bare `>=0.11` floor), `mongomock`, `pymongo>=4.6.1,<5`. Sources: PyPI `llama-index-vector-stores-azurecosmosmongo` 0.9.0 (2026-08-31) and the Learn `query-knowledge-base` page; PyPI `langchain-azure-cosmosdb` 1.0.1 and `langchain-azure-ai` 1.4.0; langchain-ai/langchain-azure PR #870 (DECISIONS.md topics 4 and 13). Add to `run-environment.md`: "Current LangChain JS: import `ChatOpenAI` from `@langchain/openai` and messages/prompts from `@langchain/core`; the old `langchain/chat_models/openai` and `langchain/schema` entrypoints and `langchain@0.0.x` are gone."
3. **`prompts/builder.md`** (after the "every workaround" line in the audit-trail list): "If the starter prompt names a framework or library and it cannot be installed or imported, stop after the second attempt, log it with `reason_source=tool_unavailable` and the error, and list it in the build report under `framework_substituted`. Never describe a prompt-required framework as optional in the README." Add `framework_substituted: list[str] = []` to `BuildReport` in `factory/models.py`.
4. **`factory/models.py` and `prompts/auditor.md`**: add cause `dependency_unavailable` ("a third-party package or language runtime failed to install or import; not a DocumentDB, Azure or MCP tool") and narrow `tool_unavailable` to "an MCP, CLI or harness tool that the run environment promised was missing or refused".
5. **`loop/findings.py`**: at line 171 map `dependency_unavailable` to a new target `pipeline`; add it to the target tuple (line 249), the target comment (line 52) and the target table in `loop/README.md`. As a stopgap for runs already recorded, route `tool_unavailable` to `pipeline` when `evidence` or `smallest_fix` matches `pip|npm|requirements\.txt|package\.json|pydantic|langchain|llama|mongomock|ETARGET|ERR_PACKAGE`.

After steps 1-2, re-run the 8 affected samples and confirm the frameworks install and the requirement lines flip to `met`.

## Evidence

- `runs/05-branch-performance-analytics/20261124-200647/decisions.jsonl` (D008) and `05-audit.json`
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/events.jsonl` (`ERR_PACKAGE_PATH_NOT_EXPORTED`) and `05-audit.json`
- `runs/10-support-ticket-rag-assistant/20261124-204529/decisions.jsonl` (D018)
- `runs/19-option-chain-data-store/20261124-192712/events.jsonl` (pydantic ForwardRef error under 3.13) and `03-build.json`
- `runs/20-provider-directory-semantic-search/20261124-200008/app/README.md` and `app/seed.py` (fallback embedder)
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/decisions.jsonl` (D027, `ETARGET`)
- `runs/14-dynamic-pricing-engine/20261124-184622/events.jsonl` (pre-0.1 `initialize_agent` import)
- `runs/16-multi-touch-attribution-model/20261124-205342/05-audit.json` (`mongomock==4.2.0` pin loosened)

## Open questions

1. Should the harness pin the venv to 3.12, or keep 3.13 and rely on the known-good pin list alone? Pinning is simpler; staying on 3.13 tests what new users are more likely to have: Learn's current Beanie and Django quickstarts (Nov 2026) require Python 3.13.x and were tested there with PyMongo 4.19.0, while `quickstart-python` says "Python 3.12 or later" (DECISIONS.md topic 4, Learn fixes). Harness maintainer decision, not an SME question.
2. Should the eight already-recorded runs be re-audited with the stopgap routing, or only re-run after the fix? The reviewer recommends re-running this group (with the harness fixes for drafts 118, 058 and 106) before any sample count is quoted externally. Harness maintainer decision, not an SME question.

No claims in this issue need DocumentDB SME confirmation; it asserts nothing about the service.

## Source drafts

- 117-build-environment-dependency-failures-langchain-llama-index-.md
