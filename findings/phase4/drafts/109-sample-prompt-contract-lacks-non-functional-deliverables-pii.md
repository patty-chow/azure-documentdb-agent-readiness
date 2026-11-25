---
title: Add a shared "gallery contract" footer to every starter prompt so the builder sees the non-functional requirements the audit already scores
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 24
findings: 33
bucket: sample-violated-practice
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add a shared "gallery contract" footer to every starter prompt

## What happens today

The pipeline scores each built sample against a "What a gallery sample also needs" section in `requirements/<sample>.md` (env-var secrets, `.env.example`, pinned dependencies, unit tests without a live cluster, IaC with the Azure DocumentDB resource type, README covering setup/run/clean-up, naming) and against practices the auditor discovers on its own (PII redaction before LLM calls and logs, monitoring, input validation, background jobs, token budgeting, provenance on AI-derived records). The builder never sees either list: `factory/agents/builder.py` `build_app` sends only the sample prompt, skill.md, the prompt-review assumptions and the readiness report, and `prompts/builder.md` only says "Include a README with what the sample shows, prerequisites, setup, how to run, and how to clean up" and "run the tests". The auditor records the resulting misses with `cause: prompt_silent` (488 such results across all `05-audit.json` files).

Approximate number of samples failing each item (`requirement_results` with status not met / partly met, plus `checks` with status violated; counts depend on how requirement names are matched):

| Requirement | Samples failing (approx.) |
|---|---|
| Unit tests run without a live cluster | ~68 |
| Dependencies pinned | ~61 |
| README clean-up section | ~42 |
| `.env.example` lists every setting | ~27-40 |
| Monitoring / diagnostics note | ~21-27 |
| PII redaction before LLM prompt or log | 6 (AML, lead scoring, wealth management, chargeback, outreach, ...) |

Note that monitoring and PII redaction are not in the shared "also needs" section today; they are discovered-practice checks, so the footer below also adds them to the scored list.

The 33 findings behind this issue (24 distinct samples) are the long tail of the same omission: the AML agent sends raw account IDs to the LLM and prints them in narratives (`aml_agent/llm.py`, `analysis.py`); the wealth-management portal serialises the whole portfolio into the prompt; the lead-scoring agent puts `lead.name`/`lead.email` in cleartext and uses `OPENAI_MODEL` in `.env.example` but `OPENAI_CHAT_MODEL` in code; the trade journal's only tests insert into the live cluster and its README has no clean-up; the returns workflow takes `orderId` from `req.body` with no validation; the AML FastAPI endpoint runs the aggregation synchronously; care-plan documents carry no provenance; RAG samples concatenate top-k passages with no token budget; pseudo-embedding demo modes and seed sizes were implemented but never logged as decisions.

## Why it matters

These are not DocumentDB knowledge gaps, so no Agent Kit skill will fix them (the kit's only redaction guidance, `skills/natural-language-querying/SKILL.md`, covers what the agent itself sends to a model while querying, not what generated app code sends), and they are the first things a gallery reviewer rejects. Because the audit list is hidden, the readiness numbers currently mix "the prompt did not say" with "the agent did not know". Telling the builder once, in a shared footer, removes the first class and makes the remaining failures the interesting ones.

## Proposed change (PR)

1. **New file `prompts/gallery_contract.md`** (appended verbatim to every starter prompt):

```
## Every gallery sample also ships
- Secrets and the connection string come only from environment variables; `.env.example` lists every variable the code reads, with placeholders, using the same names as the code.
- Dependencies are pinned to the exact versions you tested (`==` in requirements.txt / exact in package.json), and the README names the tested driver version.
- Unit tests run with no cluster (mock or in-memory driver); integration tests are a separate suite that runs only when DOCUMENTDB_URI is set. The README says how to run each.
- The README has these sections: What this shows, Prerequisites, Setup, Run, Tests, Monitoring (which cluster metrics and slow-query logs to watch, one az monitor command), Clean-up (drop the sample database, and delete the cluster with `az documentdb mongocluster delete` if you created one).
- Any data passed to a model, written to a log, or persisted in a trace is minimised first: pass only the fields the task needs, mask identifiers (last 4 chars), and state the rule in a README "Data handling" note. Mandatory when the scenario involves customer, patient or financial records.
- Request bodies and query parameters are validated (shape, length, type) before they reach a query.
- Work that aggregates or scans a collection runs as a background job with a status endpoint, not inside a request handler.
- Context sent to a chat model fits a stated token budget with an answer buffer; the heuristic is in the README.
- Documents produced by a model record provenance: model name, prompt template id, embedding model, timestamp.
- Every fallback or demo mode (pseudo-embeddings, sandbox send, seed sizes) is logged with log_decision.
- Infrastructure is provided as code using the Microsoft.DocumentDB/mongoClusters resource type.
- The service is called "Azure DocumentDB" throughout, with no former or neighbouring product name.
```

2. **`factory/agents/builder.py`, `build_app`**: in the `task` f-string (lines 25-33, after `ctx.sample_block()` and before `<skills_the_review_found_relevant>`), append `load_prompt("gallery_contract.md")` under a `<gallery_contract>` tag unless the run disables it.

3. **`main.py run`** (argparse block, lines 27-35): add `--no-contract`, carry it on `RunContext` (new `no_contract: bool` field; it does not exist today) so the prompt-only measurement stays reproducible; `loop/run_loop.py` passes it through.

4. **`loop/draft_requirements.py`, `gallery_section()`** (lines 75-80): build the shared section from `prompts/gallery_contract.md` instead of slicing `requirements/retail-semantic-search.md` from the "## What a gallery sample also needs" marker (lines 19-33 of that file), so the audit list and the footer are one file. Regenerate the shared section of the existing `requirements/*.md` files from it. While there, fix line 15 of `requirements/retail-semantic-search.md` ("Embeddings are stored as BSON binary vectors"): Azure DocumentDB vector indexes (`cosmosSearch` with vector-ivf / vector-hnsw / vector-diskann) only index embeddings stored as `number[]` arrays, so that requirement is unmeetable as written.

5. Follow-up, not in this PR: paste the same footer into the Starter Prompt column of the samples spreadsheet so published prompts carry it too.

Out of scope here (DocumentDB-specific, belong in Agent Kit skills, filed separately): projection on `find`, bulk upserts in seeds, `schemaVersion` fields, Mongoose `autoIndex:false`, atomic claim with `findOneAndUpdate`, Entra ID over SCRAM, `AsyncMongoClient` over Motor.

## Evidence

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/05-audit.json` (checks P11, P18, P20; "Unit tests run without a live cluster" not_met, cause prompt_silent)
- `runs/10-wealth-management-rag-portal/20261124-201449/05-audit.json` (checks P15, P24)
- `runs/13-algorithmic-trade-journal/20261124-191835/05-audit.json` ("Tests offline", "README clean-up instructions" violated; requirement partly_met, cause prompt_silent)
- `runs/09-lead-scoring-agent/20261124-204408/05-audit.json` (PII in prompt; OPENAI_MODEL vs OPENAI_CHAT_MODEL)
- `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json` (full record logged, unredacted outreach_logs)

## Verification

### 1. Already covered? confirmed (not there)
- `prompts/gallery_contract.md` does not exist; `prompts/builder.md` line 29 only asks for a README "with what the sample shows, prerequisites, setup, how to run, and how to clean up", line 30 says "run the tests"; nothing on offline tests, pinning, `.env.example`, PII, monitoring, validation, background jobs, token budgets or provenance.
- `factory/agents/builder.py` `build_app` (lines 25-33) does not pass `requirements/<sample>.md` or any gallery list to the builder.
- `loop/draft_requirements.py` `gallery_section()` (lines 75-80) slices the shared section out of `requirements/retail-semantic-search.md` (lines 19-33); no single source shared with the builder prompt.
- `main.py run` has no `--no-contract` flag; `RunContext` has no such field.
- Agent Kit: `skills/natural-language-querying/SKILL.md` lines 17-54 cover redacting PII the agent sends to a model while querying, not generated app code; no kit skill covers offline tests, pinned deps or README clean-up. Not a substitute.

### 2. Premise true? confirmed (with count clarifications applied)
- Recount over `runs/*/*/05-audit.json` (117 audit files): offline tests 69 samples, pinned 61, clean-up 42, `.env.example` 27-40 depending on matching, monitoring 21-27, PII 6; the draft's figures are in range, now marked approximate. `prompt_silent` is a real cause value (488 results).
- All five evidence audit files exist at the cited paths.
- Clarified that monitoring/PII are discovered-practice checks, not items in the shared "also needs" section.
- DocumentDB facts in the footer checked against the given ground truth: `az documentdb mongocluster delete` (extension CLI group), Microsoft.DocumentDB/mongoClusters, "Azure DocumentDB" naming. Added the correction for the retail requirements line claiming BSON binary vectors (vectors must be `number[]`; binary vectors are not indexed).

### 3. Maintainer skeptic: confirmed
- Names concrete files and line ranges (`prompts/gallery_contract.md`, `factory/agents/builder.py`, `main.py`, `loop/draft_requirements.py`, `requirements/*.md`), a concrete footer text, and an opt-out flag that preserves the prompt-only measurement. It belongs in the pipeline repo, since the gap is in what the harness tells the builder, not in Learn, the kit or the MCP server. Small edits applied: the missing `RunContext` field, exact line ranges, approximate counts, the IaC bullet so the footer matches the existing scored list, and the BSON-vector fix.

## Finding ids

F0030, F0032, F0033, F0244, F0064, F0208, F0653, F0656, F0688, F0590, F0624, F1548, F1746, F1747, F1517, F1582, F1585, F1552, F1648, F1710, F2147, F2148, F2179, F2506, F2512, F2615, F3066, F3100, F3099, F3171, F3138, F3201, F3355
