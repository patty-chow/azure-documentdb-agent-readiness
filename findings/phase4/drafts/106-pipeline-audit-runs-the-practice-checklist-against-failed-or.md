---
title: "Harness: log_decision rejects reason_source in 60 of 100 samples, and the audit scores empty builds as practice violations"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P0
sample_count: 5
findings: 29
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Harness: `log_decision` rejects `reason_source` in 60 of 100 samples, and the audit scores empty builds as practice violations

## What happens today

**1. The `log_decision` tool rejects the builder's calls.** The `reason_source` parameter of the tool is typed as the closed `ReasonSource` `Literal` (`prompt`, `skill`, `docs`, `tool_result`, `tool_unavailable`, `readiness_report`, `operator`, `model_default`; `factory/models.py`). Agent Framework validates tool arguments against that type *before* the function body runs, so any other value fails with `_FunctionArgumentValidationError: Invalid arguments for 'log_decision' ... Input should be 'prompt', 'skill', ...` (recorded in events.jsonl with `outcome: exception`). The `ValueError` guard in `DecisionLog.add` (`factory/decision_log.py`) is a second check that these calls never reach. gpt-5-mini writes the *name of the source* rather than the category, and retries with byte-identical arguments:

| value sent | rejected calls |
|---|---|
| `skill_md` | 41 |
| `documentdb-vector-search` | 30 |
| `documentdb-driver` | 22 |
| `assumptions_from_prompt_review` | 16 |
| `documentdb-indexing` | 11 |
| `run_policy` | 10 |
| `prompt_review` | 10 |
| 30 more variants (`skill.md`, `skill: documentdb-indexing`, `run_environment`, `guidance_for_builder`, ...) | ~60 |

Across the 120 run folders of the 100-sample experiment, **66 runs (60 distinct samples) have at least one rejected `log_decision` call**. `run_policy` is notable: there is no literal for "the run environment told me" (`operator` is meant to cover it, but nothing says so).

**2. Three rejections in a row switch tools off, and the audit runs anyway.** Agent Framework's default `max_consecutive_errors_per_request` is 3. Five builds hit three rejections consecutively, made **zero further tool calls**, left `app/` empty and returned `status: "partial"` (never `"failed"`):

- `runs/07-customer-review-sentiment-pipeline/20261124-183656`
- `runs/07-multi-currency-ledger/20261124-190814`
- `runs/09-inventory-reorder-multi-agent-system/20261124-184020`
- `runs/13-product-q-a-chatbot-rag/20261124-184527`
- `runs/19-cross-sell-recommendation-beanie/20261124-185532`

`factory/pipeline.py` line 223 skips the audit only when `build.status == "failed"`, so stage 5 ran the full practice checklist against an empty workspace and emitted **29 `violated` checks whose evidence is "no code present"**. The 13-product-q-a run alone has 14: singleton client, vector index, `number[]` embeddings, chunking, top-k, TLS, secrets, retries, timeouts, all "violated" by absence. Its rerun (`20261125-055422`) wrote 11 files and passed with findings, confirming the first run was a harness failure, not a sample finding.

**3. In runs that did produce code, the audit trail is wrongly flagged.** Because the index-shape and provisioning decisions were rejected, they never landed in `decisions.jsonl`, and the auditor then marked the sample as violating "record index-shape decisions" (04-customer-journey-mapper check *Audit trail: index decision*, 07-customer-review *Audit trail: index plan*, 13-product-q-a *Audit trail: vector-index choice*). The builder itself noticed: 02-transaction-categorization's `open_issues` says a few decision-logging calls "failed ... due to transient invocation errors".

**4. Builder deviations from the prompt go unlogged.** 06-credit-risk-multi-agent-scorer: the prompt asks for a "Python LangChain multi-agent pipeline"; `app/requirements.txt` pins `langchain>=0.0.300`, the README mentions it, but no `.py` file imports it and `decisions.jsonl` (D001-D012) has no framework decision.

## Why it matters

These are harness defects that show up in the results as *sample* findings. In the "violated practice" bucket, 29 of the findings (5 samples) are pure artifacts of items 1-2 above, and the 60-sample rejection rate means decision-log statistics (`model_default` share, audit-trail completeness) are unreliable for the whole experiment. Anyone reading `05-audit.md` for 13-product-q-a would conclude the agent does not know to use `number[]` embeddings or `cosmosSearch` indexes, when in fact it never got to write code.

## Proposed changes

**(a) `factory/decision_log.py` - do not raise; normalize and describe.**

```python
_ALIASES = [
    (("skill", "documentdb-"), "skill"),
    (("prompt_review", "assumptions_from_prompt_review", "assumption", "readiness"), "readiness_report"),
    (("run_policy", "run_environment", "guidance_for_builder", "guidance"), "operator"),
    (("learn", "docs", "documentation"), "docs"),
]

def normalize_reason_source(raw: str) -> str | None:
    v = (raw or "").strip().lower()
    if v in get_args(ReasonSource):
        return v
    for prefixes, target in _ALIASES:
        if v.startswith(prefixes):
            return target
    return None
```

The essential change is the parameter type: as long as `reason_source` is annotated as the `Literal`, the framework rejects the call during argument validation and nothing inside `tool_for` runs. Annotate it as `str`, then in `tool_for` normalize and return a *string* for unmappable values (and drop or relax the `ValueError` in `DecisionLog.add`) so a bad value never counts toward the framework's consecutive-error budget:

```python
src = normalize_reason_source(reason_source)
if src is None:
    return ("Not recorded. reason_source is a CATEGORY, one of: " + ", ".join(get_args(ReasonSource)) +
            ". Name the skill or document in `evidence`, then call log_decision again.")
entry = log.add(stage, decision, reason, src, alternatives, evidence, reason_source_raw=reason_source)
```

Add `reason_source_raw: str = ""` to `Decision` in `factory/models.py` so the original wording is kept for analysis. Keep `Decision.reason_source` typed as `ReasonSource` (the normalized value always fits it). The enum in the tool schema did not stop the model; the hard rejection is what causes the damage. Rewrite the Field description:

> A category, not the name of a document. `prompt` = the sample prompt said so; `skill` = an installed skill said so (name it in evidence); `docs` = a documentation page; `tool_result` = something you observed by running a tool; `tool_unavailable` = forced by a missing/failing tool; `readiness_report` = a correction or assumption from the prompt review / readiness stage; `operator` = the run policy or run environment; `model_default` = nothing told you.

Optionally add a `run_policy` literal, since 10 rejections used exactly that word.

**(b) `factory/llm.py` `_make_client` - raise the error budget.**

```python
loop = {"max_iterations": max_iterations or settings.max_iterations, "max_consecutive_errors_per_request": 10}
```

The fork used for this experiment already carries this one-line change (with a comment in `_make_client`); the reruns made with it produced code. Upstream it still needs to land.

**(c) `factory/pipeline.py` - detect an incomplete build before auditing.** After stage 3, treat these as `build_incomplete` and exit with `EXIT_BUILD_FAILED` instead of running stages 5a/5:

```python
app_files = [p for p in (run_dir / "app").rglob("*") if p.is_file()]
touches_db = any(re.search(r"DOCUMENTDB_URI|MongoClient|mongodb\+srv", p.read_text(errors="ignore"))
                 for p in app_files if p.suffix in {".py", ".js", ".ts", ".java", ".cs", ".go"})
if not app_files or not build.files_created or (build.status == "partial" and not touches_db):
    say("      The build produced no runnable app; recording build_incomplete instead of auditing.")
    verdicts["build"] = "build_incomplete"
    return finish(EXIT_BUILD_FAILED, verdicts)
```

Belt and braces: `prompts/auditor.md` line 67 already requires "cite the file and line" for `violated`. Enforce it with a validator on `AuditCheck` that downgrades a `violated` check whose `evidence` contains no path-like token (`\w+\.(py|js|ts|json|md|yaml|txt)`) to `not_assessable`, with a note.

**(d) Post-build framework check.** Extract framework names from `prompt.md` (`langchain`, `langgraph`, `semantic kernel`, `autogen`, `beanie`, `motor`, `mongoose`, `spring data`, ...), compare against the manifest *and* actual imports in `app/`. If a name appears in the prompt but in no import, require a matching decision in `decisions.jsonl`; otherwise the pipeline appends an `audit trail` check itself (`availability: discovered_not_listed`, category `audit trail`) so the deviation is recorded even when the auditor misses it.

## Evidence

- `runs/13-product-q-a-chatbot-rag/20261124-184527/events.jsonl` lines 19-21 (three `_FunctionArgumentValidationError` rejections, `reason_source=documentdb-vector-search`, then silence); `03-build.json` `files_created: []`, `status: partial`; `05-audit.json` 14 violated, verdict `fail`. Rerun `runs/13-product-q-a-chatbot-rag/20261125-055422/` 11 files, `pass_with_findings`.
- `runs/09-inventory-reorder-multi-agent-system/20261124-184020/events.jsonl` lines 18-20 (`reason_source=run_policy` x3); `05-audit.json` 7 violated, evidence "app/ empty".
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/events.jsonl` lines 29-31 (identical arguments resent twice); 7 violated on zero files.
- `runs/04-customer-journey-mapper/20261124-203553/events.jsonl` lines 21-23 (provisioning decision rejected x3; code exists, audit-trail check still `violated`).
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (`prompt.md` line 1 asks for LangChain; `app/requirements.txt` pins it; no `.py` imports it; no framework decision in `decisions.jsonl`).

## Verification

### 1. Already covered? partially_covered
- `factory/llm.py` `_make_client` in the experiment's fork already sets `"max_consecutive_errors_per_request": 10`, with the comment "the framework's default of 3 switched the builder's tools off after three malformed log_decision calls in a row". `loop/README.md` line 117 documents it ("the library default is 3"). So change (b) exists in the fork; it is not yet confirmed upstream.
- Not covered: `factory/models.py` still types `reason_source` as the closed `ReasonSource` Literal and `factory/decision_log.py` `tool_for` still annotates the parameter with it (change a). `factory/pipeline.py` line 223 skips the audit only on `build.status == "failed"`, with no `files_created` or empty-`app/` check and no `build_incomplete` verdict (change c). There is no framework-versus-imports check (change d). `prompts/auditor.md` requires "cite the file and line" for `violated` but nothing enforces it.

### 2. Premise true? confirmed (one mechanism corrected in the body)
- Counted again across `runs/*/*/events.jsonl`: 120 run folders, 66 with at least one failed `log_decision` call, 60 distinct samples. Matches the draft.
- The five empty builds have `03-build.json` `status: partial` and `files_created: []`, an empty `app/`, and `05-audit.json` verdict `fail` with 14 + 7 + 7 + 0 + 1 = 29 `violated` checks. Matches the draft's 29.
- Correction applied: the rejection does not come from `DecisionLog.add` raising `ValueError`. events.jsonl shows `_FunctionArgumentValidationError: Invalid arguments for 'log_decision' ... Input should be 'prompt', 'skill', ...`, which Agent Framework raises while validating arguments against the `Literal` annotation, before the body runs. The body now says the type change to `str` is the essential fix, and that changing only the `raise` in `tool_for` would not help.
- Line reference corrected: in the fork the error-budget line is in `_make_client` (line 37), not line 34.
- No Azure DocumentDB facts are asserted beyond `number[]` embeddings and `cosmosSearch` indexes, which are correct.

### 3. Maintainer skeptic: confirmed
- Right repository (the harness). Names the files and functions (`factory/models.py` `ReasonSource`, `factory/decision_log.py` `tool_for`/`add`, `factory/llm.py` `_make_client`, `factory/pipeline.py` stage-4 gate, `prompts/auditor.md`). Gives concrete code and reproducible run evidence. The defect skews the experiment's DocumentDB readiness results (5 samples scored on empty workspaces, decision-log statistics for 60 samples), so it is more than generic hygiene. A maintainer might split (d) into its own issue.

## Finding ids

- F0552
- F1027
- F1029
- F1030
- F1031
- F1033
- F0912
- F1035
- F1457
- F1458
- F1459
- F1460
- F1461
- F1462
- F1463
- F2270
- F2271
- F2272
- F2273
- F2274
- F2275
- F2276
- F2277
- F2278
- F2279
- F2280
- F2281
- F2282
- F2283
