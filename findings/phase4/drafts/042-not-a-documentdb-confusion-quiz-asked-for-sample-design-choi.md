---
title: "Readiness stage files sample design choices as learn-docs confusions: add a 'design_choice' outcome and constrain S01-S05 to service facts"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P1
sample_count: 20
findings: 29
bucket: confusion-sample-specific
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness stage files sample design choices as learn-docs confusions

## What happens today

`prompts/readiness_cold.md` asks the model to add up to five answers `S01`-`S05` stating "a service-specific fact you would rely on to build this particular sample". In practice gpt-5-mini writes questions whose answers are free design choices of the sample author that the one-paragraph sample prompt never fixes:

- database and collection names ("What exact database and collection names will this sample use?")
- the seed document schema, field names, and whether the seed is idempotent
- which embedding model and dimensionality the sample will assume
- pinned `requirements.txt` / LlamaIndex / `langchain-azure-ai` / provider SDK versions
- `DOCUMENTDB_URI` vs `MONGODB_URI` as the env var name
- how to constrain the LLM categorisation prompt to a taxonomy, whether to compute drawdown with `$setWindowFields` or client-side, how to implement a stale-while-revalidate CAS flag, what PII to redact before persisting LLM evidence
- the exact DocumentDB MCP tool names a verification script should call

The checker (`prompts/readiness_checker.md`) has no outcome for "this is not a service fact", so it grades these `could_not_verify` or `partly_wrong` with `confused_with: none`, and often says so in its own words: the `08-insurance-pre-auth` S02 record's `build_risk` reads "these are implementer choices rather than authoritative facts from product docs ... this is a design choice, not a platform mismatch"; the `20-open-banking` S04 record's `why_the_confusion_arose` reads "This is a design-level proposal rather than a service fact".

Downstream, every layer then treats the item as missing Azure DocumentDB knowledge:

| File | Effect |
|---|---|
| `factory/scoring.py` `KNOWLEDGE_CREDIT` | `could_not_verify` scores 0.0 and stays in the denominator, so the readiness knowledge score drops for a question no document could answer; `_grounded()` returns False, so the grounding score drops too |
| `factory/aggregate.py` lines 55-60 | item is appended to `unverifiable[...]` and reported alongside real doc gaps |
| `factory/reports.py` | counted in "N could not be verified" in the per-run readiness report |
| `loop/findings.py` line 92 (fork only) | `target="learn-docs" if c.get("confused_with") in ("none", "unknown") else "learn-docs"`: both branches yield `learn-docs`, so the item becomes a Learn-docs confusion in `findings/TRIAGE.md` |

## Why it matters

- 29 records in the current triage bucket, from 20 of the 100 samples, propose Learn-docs or Agent Kit changes ("README naming conventions", "required sample schema section", "pinned requirements.txt", "privacy note") that are per-sample README content, not product gaps. They pad the doc-gap backlog and the readiness failure count that the PM reads.
- Across all 120 readiness reports the pattern (S-item, non-`correct`, `confused_with: none`) occurs 66 times in 43 samples; restricted to each sample's latest run it is 56 items in 38 of 101 samples. The 11 Q-items are not affected (32 cases over 2,300 answers), so this is specific to the free-form S-items.
- Nothing here contradicts a DocumentDB fact. Two items could be answered by existing material (MCP tool names by the `microsoft/documentdb-mcp` README tool table; `$setWindowFields` by a feature-compatibility note) but neither is a wrong belief that needs correcting.

## Proposed change

1. **`prompts/readiness_cold.md`** - replace the S01-S05 paragraph with:
   > Each S item states a fact about the service that a Learn page, an installed skill or an MCP tool description could confirm or refute: an index definition, an aggregation operator's availability, an auth flow, a connection-string option, a supported server version. Do not write questions whose answer is your own design choice for this sample: database or collection names, document shape or field names, seed data, embedding model or dimensions, package versions, environment variable names, prompt wording, or application logic. If the prompt leaves such a choice open, it is a choice, not a fact; leave it out.

2. **`factory/models.py`** - extend `Confusion.outcome` with `"design_choice"`, and **`prompts/readiness_checker.md`** - add to the grading list:
   > `design_choice` - the cold answer is a sample-design decision (a name, schema, version, model or application pattern) that no service documentation prescribes. State that in `grounded_answer`, set `confused_with` to `none`, leave `improvements` empty. This is neither a confusion nor a documentation gap.

3. **`factory/scoring.py`** - exclude `design_choice` from `n` in both the knowledge and grounding components (compute over `[c for c in confusions if c.outcome != "design_choice"]`); keep `could_not_verify` at 0.0 so genuine doc gaps still count.

4. **`factory/aggregate.py`** and **`factory/reports.py`** - collect `design_choice` items in their own "Sample decisions left open by the prompt" list instead of `unverifiable` / "could not be verified".

5. **`loop/findings.py` (fork only: `loop/` exists in the patty-chow fork, not in upstream `main`; land this item there, items 1-4 and 6 upstream)** - at line 92 route `confused_with == "none"` and `outcome in ("could_not_verify", "partly_wrong", "design_choice")` to `target="sample"`, `kind="sample_decision"`, so they reach the sample-prompt row of `TRIAGE.md`, not Learn docs. Until (2) ships, this alone removes the 29 records from the learn-docs bucket.

6. **Secondary, `samples/<vertical>/*.md`** - add an optional `Fixed choices` block (collection names, minimal document shape, embedding model and dims, `DOCUMENTDB_URI`) so that any S-item about them has a ground truth. `loop/run-environment.md` already fixes the database name this way; this extends the same idea.

## Evidence

- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` confusions[S02] (outcome `partly_wrong`, `confused_with: none`; `build_risk` says "design choice, not a platform mismatch")
- `runs/20-open-banking-api-cache-layer/20261124-192737/02-readiness.json` confusions[S02, S04]
- `runs/14-hyper-personalized-content-engine/20261124-205043/02-readiness.json` confusions[S04, S05]
- `runs/02-transaction-categorization-agent/20261124-190028/02-readiness.json` confusions[S01, S04, S05]
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json` confusions[S02, S04, S05]

## Verification

### 1. Already covered? - confirmed (not there)
The target is the experiment harness, so the check is against the local checkout (`main`/`samples-loop` of the fork, upstream `abinav2307/azure-documentdb-agent-readiness`). `grep -rn "design_choice|sample_decision|design choice" factory loop prompts` returns nothing. `factory/models.py` line 98 defines `outcome: Literal["correct", "outdated", "partly_wrong", "wrong", "could_not_verify"]` with no design-choice outcome; `prompts/readiness_checker.md` line 29 offers only `could_not_verify` ("you searched and found no source that answers the question"). `prompts/readiness_cold.md` line 9 places no restriction on S01-S05 beyond "a service-specific fact you would rely on to build this particular sample". Nothing in the harness implements the ask.

### 2. Is the premise true? - confirmed
Each code claim was checked against the source:
- `factory/scoring.py` line 30: `KNOWLEDGE_CREDIT = {..., "could_not_verify": 0.0}`; line 76 divides by `n` over all confusions; `_grounded()` (lines 59-61) returns False for `could_not_verify`.
- `factory/aggregate.py` lines 55-60: `could_not_verify` items are appended to `unverifiable[...]`.
- `factory/reports.py` line 89: "... could not be verified." count.
- `loop/findings.py` line 92: `target="learn-docs" if c.get("confused_with") in ("none", "unknown") else "learn-docs"` - both branches yield learn-docs, as stated.
- `loop/run-environment.md` line 6 fixes the database name (`{database}`) and line 5 names `DOCUMENTDB_URI`, supporting item 6.
- `loop/` is absent from `upstream/main` (git ls-tree), confirming the "fork only" label; the draft now says where item 5 lands.
- Quotes: in `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` the phrase "design choice, not a platform mismatch" is in S02's `build_risk` (outcome partly_wrong, confused_with none); in `runs/20-open-banking-api-cache-layer/20261124-192737/02-readiness.json` "design-level proposal rather than a service fact" is in S04's `why_the_confusion_arose` (outcome could_not_verify). Field names were added to the body.
- The 29 finding ids map to 20 distinct samples, all with target learn-docs (scratchpad `phase4/findings-default.json`).
No Azure DocumentDB fact is asserted beyond what the fixed facts allow; the draft makes no service claim to correct.

### 3. Maintainer skeptic - confirmed
As maintainer of the harness I would accept this: it names exact files and lines, gives replacement prompt text, a schema change, a scoring rule and a routing fix, and includes an obvious bug (identical ternary branches in `loop/findings.py`). The DocumentDB angle is direct: it stops sample-design questions from being filed as Azure DocumentDB Learn-docs gaps and from lowering the readiness knowledge score. Small edit applied: item 5 is scoped to the fork, since `loop/` does not exist upstream.

## Finding ids
- F0223
- F0323
- F0325
- F0326
- F0465
- F0638
- F0640
- F0666
- F0667
- F0802
- F1049
- F1207
- F1233
- F1691
- F1834
- F1837
- F1899
- F2130
- F2194
- F2254
- F2366
- F2397
- F2398
- F2850
- F2984
- F2985
- F2986
- F3434
- F3435
