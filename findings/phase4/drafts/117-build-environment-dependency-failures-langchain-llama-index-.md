---
title: "Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs; audit then charges \"framework dropped\" to documentdb-mcp"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P2
sample_count: 8
findings: 13
bucket: mcp-server
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Harness: Python 3.13 venv breaks LangChain/LlamaIndex installs, and the audit charges "framework dropped" to documentdb-mcp

## What happens today

`loop/run_loop.py` creates each run's venv with `PYTHON = sys.executable` (line 56; `make_venv` at lines 212-215). On the experiment host that is Python 3.13. Consequences seen in the 100-sample run:

- `pip install langchain` resolved to a pydantic-core release with no prebuilt cp313 wheel for the host, so pip tried to build it from source with Rust; the build failed and the builder removed LangChain (`05-branch-performance-analytics`, decision D008: "pydantic-core build that failed in this environment (Rust toolchain error)"). Current pydantic-core releases do ship cp313 wheels, so this is an old-pin plus new-interpreter mismatch.
- The pinned `llama-index==0.9.2` / `0.10.0` dependency chains did not install under 3.13; the builder removed LlamaIndex and wrote direct OpenAI calls plus a deterministic fallback embedder, then documented LlamaIndex as optional (`10-support-ticket-rag-assistant` D018, `20-provider-directory-semantic-search` README and `app/seed.py`).
- Pydantic v1 (`pydantic==1.10.12`, `fastapi==0.95.2`) cannot be imported under 3.13 (`ForwardRef._evaluate() missing 1 required keyword-only argument`), so the offline FakeCollection unit tests were never executed (`19-option-chain-data-store`).
- `mongomock==4.2.0` failed to install, so the exact pin was loosened to `>=4.2.0` (`16-multi-touch-attribution-model`).

A second cause is model-side, not runtime-side: gpt-5-mini targets LangChain's pre-0.1 surface. Python: `from langchain.agents import initialize_agent, AgentType` (`14-dynamic-pricing-engine`). Node: `require('langchain/chat_models/openai')` and `require('langchain/schema')` -> `ERR_PACKAGE_PATH_NOT_EXPORTED`, because those entrypoints no longer exist in current `langchain` releases (`18-returns-refund-workflow-orchestration`), and `langchain@^0.0.275` -> npm `ETARGET` (`18-chargeback-dispute-multi-agent` D027). In every case the builder replaced the framework with the OpenAI SDK.

The auditor graded all of these `partly_met`/`not_met` with `cause=tool_unavailable`, the closest value in `factory/models.py` `RequirementResult.cause`. Then `loop/findings.py` line 171 does:

```python
"agent-kit" if r["cause"] == "skill_silent" else "documentdb-mcp",
```

so 13 requirement findings about pip/npm packages were filed against the DocumentDB MCP server bucket.

## Why it matters

- 8 of 100 samples (13 requirement findings) lost the framework the prompt required. Those samples now teach developers "use the OpenAI SDK and treat LangChain/LlamaIndex as optional", which is not what the gallery author asked for, and one of them ships a fake embedder as the default path.
- The 13 findings pollute the `mcp-server` bucket; a maintainer of microsoft/documentdb-mcp would reject every one. Nothing in them involves DocumentDB or the MCP server.
- Requirement-met counts in `factory/pipeline.py` and `factory/aggregate.py` debit the kit and MCP server for a harness problem.

## Proposed change

1. **`loop/run_loop.py`** - add `--python PATH` (default: `shutil.which("python3.12") or shutil.which("python3.11")`, error if neither is found; python3.12 is present on the experiment host) and use it in `make_venv` instead of `sys.executable`. Keep `sys.executable` for launching `main.py`. Add the resolved version to the rendered `loop/run-environment.md` ("`python` is CPython 3.12.x").
2. **Pre-warm the venv** in `make_venv` with a tested pin list stored at `loop/known-good-pins.txt` (installed with `pip install -q -r`): `pydantic>=2.7`, `fastapi`, `langchain>=0.3`, `langchain-openai`, `langchain-community`, `llama-index>=0.11`, `llama-index-vector-stores-azurecosmosmongo`, `mongomock`, `pymongo`. For Node, add one line to `run-environment.md`: "Current LangChain JS: import `ChatOpenAI` from `@langchain/openai` and messages/prompts from `@langchain/core`; the old `langchain/chat_models/openai` and `langchain/schema` entrypoints and `langchain@0.0.x` are gone." This also corrects the stale-API prior without touching the kit.
3. **`prompts/builder.md`** (after the "every workaround" line in the audit-trail list) - "If the starter prompt names a framework or library and it cannot be installed or imported, stop after the second attempt, log it with `reason_source=tool_unavailable` and the error, and list it in the build report under `framework_substituted`. Never describe a prompt-required framework as optional in the README." Add `framework_substituted: list[str] = []` to `BuildReport` in `factory/models.py`.
4. **`factory/models.py` + `prompts/auditor.md`** - add cause `dependency_unavailable` ("a third-party package or language runtime failed to install or import; not a DocumentDB, Azure or MCP tool") and narrow `tool_unavailable` to "an MCP, CLI or harness tool that the run environment promised was missing or refused".
5. **`loop/findings.py` line 171** - map `dependency_unavailable` to a new target `pipeline` (add it to the target tuple on line 249, the target comment on line 52, and `loop/README.md`'s target table). As a stopgap for already-recorded runs, route `tool_unavailable` to `pipeline` when `evidence` or `smallest_fix` matches `pip|npm|requirements\.txt|package\.json|pydantic|langchain|llama|mongomock|ETARGET|ERR_PACKAGE`.

After (1)-(2), re-run the 8 affected samples to confirm the frameworks install and the requirement lines flip to `met`.

## Evidence

- `runs/05-branch-performance-analytics/20261124-200647/decisions.jsonl` (D008) and `05-audit.json` requirement_results
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/events.jsonl` (ERR_PACKAGE_PATH_NOT_EXPORTED) and `05-audit.json`
- `runs/10-support-ticket-rag-assistant/20261124-204529/decisions.jsonl` (D018)
- `runs/19-option-chain-data-store/20261124-192712/events.jsonl` (pydantic ForwardRef TypeError under python3.13) and `03-build.json` builder_report
- `runs/20-provider-directory-semantic-search/20261124-200008/app/README.md`, `app/seed.py` (fallback embedder)
- Also: `runs/18-chargeback-dispute-multi-agent/20261124-192501/decisions.jsonl` (D027, ETARGET), `runs/14-dynamic-pricing-engine/20261124-184622/events.jsonl`, `runs/16-multi-touch-attribution-model/20261124-205342/05-audit.json`

## Verification

### 1. Already covered? confirmed (not covered)
Target is the harness repo. Grepped `loop/`, `prompts/`, `factory/` for `framework_substituted`, `dependency_unavailable`, `known-good`, `--python`, `python3.12`, `langchain`: no matches. `loop/run_loop.py` line 56 is `PYTHON = sys.executable` and line 214 builds the venv with it. `loop/run-environment.md` line 7 only says `python` and `pip` resolve to a per-run venv, with no version or pins. `factory/models.py` `RequirementResult.cause` has no dependency-specific value. Nothing in the target implements the ask.

### 2. Premise true? confirmed (wording corrected)
- `loop/findings.py` line 171 maps every non-`skill_silent` cause (i.e. `tool_unavailable`) to `documentdb-mcp`: verified verbatim.
- `RequirementResult.cause` values (`factory/models.py` lines 329-337) include `tool_unavailable` ("a missing or refused tool prevented it") and nothing for third-party packages: verified.
- D008 text cites a pydantic-core build failure with a Rust toolchain error; `19-option-chain-data-store` events reference python3.13; `18-returns-refund` events contain ERR_PACKAGE_PATH_NOT_EXPORTED; `18-chargeback` events/decisions contain ETARGET: verified in run files.
- Corrections applied: (a) the draft said pydantic-core "has no 3.13 wheel"; current pydantic-core releases publish cp313 wheels, so the failure is an old resolved pin without a cp313 wheel, reworded accordingly. (b) The draft said "LangChain JS is ESM-only" and required `"type":"module"`; @langchain packages also publish CommonJS builds, and the error comes from removed entrypoints (`langchain/chat_models/openai`, `langchain/schema`), so the Node note now points at `@langchain/openai` / `@langchain/core` instead. (c) llama-index claim softened to "pinned dependency chains did not install under 3.13" rather than asserting no compatible release exists. (d) `--python` default fallback written as `shutil.which("python3.11")`; python3.12 confirmed present on the host.
- No Azure DocumentDB facts are asserted; nothing contradicts the service facts.

### 3. Maintainer skeptic: confirmed
As the harness maintainer I would accept this: it names exact files and lines (`loop/run_loop.py` 56/212-215, `loop/findings.py` 171/249, `factory/models.py` RequirementResult/BuildReport, `prompts/builder.md`, `prompts/auditor.md`), gives concrete code-level changes, and directly fixes the readiness scoring (findings misrouted to the DocumentDB MCP bucket). It belongs in this repo, not microsoft/documentdb-mcp or the agent kit.

## Finding ids

- F0758
- F0759
- F1712
- F2383
- F2740
- F3067
- F3102
- F3103
- F3104
- F3105
- F3319
- F3492
- F3493
