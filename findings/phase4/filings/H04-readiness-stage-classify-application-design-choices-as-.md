---
id: H04
title: "Readiness stage: classify application design choices as builder decisions, not learn-docs gaps"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 35
member_drafts:
  - 054-readiness-stage-mis-targets-application-design-decisions-as-.md
  - 042-not-a-documentdb-confusion-quiz-asked-for-sample-design-choi.md
open_questions: 3
---

# Readiness stage: classify application design choices as builder decisions, not learn-docs gaps

> This repository belongs to a colleague; coordinate with the maintainer before opening this PR.

## What happens today

The readiness stage has two places where the model reports what it does not know, and neither can say "this is a choice the sample author leaves open, not a missing product fact".

1. **Information gaps.** `prompts/readiness_checker.md` (line 41) asks for "what the builder will need to know for this sample that no skill, doc or tool answered". `InformationGap` in `factory/models.py` (line 136) has only `title` and `description`.
2. **S01-S05 cold answers.** `prompts/readiness_cold.md` (line 9) asks for "a service-specific fact you would rely on to build this particular sample", with no further limits. The checker can grade these only `correct`, `outdated`, `partly_wrong`, `wrong` or `could_not_verify` (`Confusion.outcome`, `factory/models.py` line 98).

With gpt-5-mini both lists fill up with application design choices: collection and field names, document shapes, seed data contents and counts, scoring formulas, which news feed, SMS provider or CLIP checkpoint to use, REST routes and payloads, retention defaults, embedding model and dimensions, pinned package versions, env var names, agent memory patterns. The model often says so itself, for example "this is a design decision the builder must supply" and "a design-level proposal rather than a service fact".

Downstream, every layer treats them as missing Azure DocumentDB knowledge:

| Code | Effect |
|---|---|
| `loop/findings.py` lines 100-108 | every information gap becomes a `learn-docs` finding, "Document this where the agent looked." |
| `loop/findings.py` line 92 | `target="learn-docs" if ... in ("none", "unknown") else "learn-docs"`: both branches give `learn-docs` |
| `factory/scoring.py` lines 107-108 | `GAP_PENALTY` subtracted for every gap |
| `factory/scoring.py` line 30, 59-61, 76 | `could_not_verify` scores 0.0, stays in the denominator and fails `_grounded()` |
| `factory/aggregate.py` 55-60, `factory/reports.py` 89 | listed and counted as "could not be verified" |

The decision log (`log_decision`, `reason_source="model_default"`, `factory/aggregate.py` line 138) is the right home for these, but nothing routes them there.

## Why it matters

- In one experiment run (100 samples, 120 runs, gpt-5-mini), 51 findings from **35 of the 100 samples** were application design choices filed as Learn-docs gaps or confusions (22 information gaps from 17 samples, 29 cold-answer items from 20 samples; 2 samples appear in both). Counts are from that single run and will shift on re-run.
- Wider pattern, same run: a keyword pass suggests roughly half of all 461 information-gap entries are design choices (an estimate); S-items graded non-`correct` with `confused_with: none` occur 66 times in 43 samples. Q-items are unaffected.
- Learn maintainers must discard these by hand to reach the real gaps in the same bucket. Readiness scores penalise open-ended prompts, so scores are not comparable across samples. The auditor sees each choice twice and loses the "invented default" signal in the decision log.

## Proposed change

**1. `factory/models.py`**

```python
class InformationGap(BaseModel):
    kind: Literal["documentation_gap", "builder_decision"] = Field(
        default="documentation_gap",
        description=(
            "documentation_gap: a fact about Azure DocumentDB, its tools or SDKs that the builder needs and "
            "no skill, doc or tool states (e.g. 'IVF parameter sizing', 'which PyMongo versions are supported'). "
            "builder_decision: an application design choice the prompt left open and that no service documentation "
            "could prescribe (document shapes, seed data contents or counts, scoring formulas, third-party providers, "
            "API route shapes, retention defaults, agent framework patterns)."
        ),
    )
    title: str = ...
    description: str = ...
```

and extend `Confusion.outcome` with `"design_choice"`. Both defaults keep existing `02-readiness.json` files loading; `_older_files` needs no edit.

**2. `prompts/readiness_cold.md`**: replace the S01-S05 paragraph with:

> Each S item states a fact about the service that a Learn page, an installed skill or an MCP tool description could confirm or refute: an index definition, an aggregation operator's availability, an auth flow, a connection-string option, a supported server version. Do not write questions whose answer is your own design choice for this sample: database or collection names, document shape or field names, seed data, embedding model or dimensions, package versions, environment variable names, prompt wording, or application logic. If the prompt leaves such a choice open, it is a choice, not a fact; leave it out.

**3. `prompts/readiness_checker.md`**: add to the grading list:

> `design_choice` - the cold answer is a sample-design decision (a name, schema, version, model or application pattern) that no service documentation prescribes. State that in `grounded_answer`, set `confused_with` to `none`, leave `improvements` empty. This is neither a confusion nor a documentation gap.

and replace the Information gaps paragraph with:

> **Information gaps.** List what the builder will need to know for this sample that no skill, doc or tool answered. Set `kind`:
> - `documentation_gap` when the missing item is a fact about Azure DocumentDB, its CLI, SDKs, MCP server or agent kit that a product page or skill could state. Example titles: "IVF parameter sizing", "Driver version support".
> - `builder_decision` when the prompt left an application design choice open and no service documentation could reasonably prescribe it: collection and field names, seed data contents, counts or licence, scoring formulas, which external provider or feed to use, REST route and payload shapes, retention defaults, agent framework or memory patterns. Name the choice in `title` so the builder can log it with `log_decision` (`reason_source: model_default`) when it decides; do not describe it as missing documentation.
>
> Give each a short `title` and a `description` of what is missing and where you looked.

**4. `factory/scoring.py`**: penalise only documentation gaps, and drop design choices from the knowledge and grounding denominators (`could_not_verify` stays 0.0):

```python
gaps = [g.title or g.description for g in report.information_gaps if g.kind == "documentation_gap"]
scored = [c for c in confusions if c.outcome != "design_choice"]  # use for n in both components
```

**5. `factory/aggregate.py` and `factory/reports.py`**: collect `design_choice` items in a "Sample decisions left open by the prompt" list instead of `unverifiable` / "could not be verified"; optionally add a kind column to the information-gaps table (`reports.py` line ~123).

**6. `loop/findings.py`** (see open question 1): route both kinds to the sample, and fix the identical ternary at line 92 so `confused_with == "none"` with outcome `could_not_verify`, `partly_wrong` or `design_choice` gets `target="sample"`, `kind="sample_decision"`, so they reach the sample-prompt row of `TRIAGE.md`. Until steps 1-3 ship, this routing alone moves the 29 cold-answer records out of the learn-docs bucket. For gaps:

```python
for g in readiness.get("information_gaps", []):
    if isinstance(g, str):
        g = {"title": "", "description": g}
    if g.get("kind") == "builder_decision":
        out.append(Finding(
            sample, rel, "readiness", "builder_decision", "sample", "low",
            topic=(g.get("title") or g.get("description", ""))[:120],
            detail=g.get("description", ""),
            proposed_change="Design choice left to the builder; expected in decisions.jsonl with reason_source=model_default. No doc target.",
            evidence=f"{rel}/02-readiness.json information_gaps",
        ))
        continue
    out.append(Finding(sample, rel, "readiness", "information_gap", "learn-docs", "medium", ...))  # unchanged
```

Add `builder_decision` and `sample_decision` to the `kind` comment on line 51.

**7. `tests/test_units.py`**: one `ReadinessReport` fixture with a gap of each kind and one `design_choice` confusion; assert one `learn-docs` and one `sample` finding per pair, a gap penalty of 1, `design_choice` excluded from `n`, and that legacy entries without `kind` (including the bare-string form at line ~196) parse as `documentation_gap`. Existing `InformationGap(title=..., description=...)` constructions keep working.

**8. Optional, `samples/<vertical>/*.md`**: an optional `Fixed choices` block (collection names, minimal document shape, embedding model and dims, `DOCUMENTDB_URI`), extending what `loop/run-environment.md` already does for the database name.

Out of scope: a generic seed-data recipe for the agent kit's data-modeling skill would answer many seed-data entries; that belongs in Azure/documentdb-agent-kit.

## Evidence

- `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json` (information gap "Risk scoring formula and narrative template")
- `runs/11-preference-center-consent-store/20261124-204614/02-readiness.json` (gaps "Retention period policy", "Exact request/response JSON shapes & route names")
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json` (gaps "Exact collection schema & field names", "Seed sample data set")
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/02-readiness.json` (confusion S02, `build_risk`)
- `runs/20-open-banking-api-cache-layer/20261124-192737/02-readiness.json` (confusions S02, S04)
- `runs/02-transaction-categorization-agent/20261124-190028/02-readiness.json` (confusions S01, S04, S05)

## Open questions

This change makes no claims about Azure DocumentDB itself, so no item needs SME confirmation, and the retryWrites question does not arise. DECISIONS.md (2026-11-25) records no settled or open SME item that touches this filing; the three items below are maintainer decisions for the harness repository.

1. `loop/` exists only in the samples-loop fork, not upstream `main`. Should step 6 land in the fork, with steps 1-5 and 7-8 upstream?
2. Should the two labels share one name (`builder_decision` for gaps, `design_choice` for confusions), so reports and triage group them together?
3. Should design choices drop out of scoring entirely (as proposed), or keep a small penalty so a vague sample prompt still shows up?

## Source drafts

- 054-readiness-stage-mis-targets-application-design-decisions-as-.md
- 042-not-a-documentdb-confusion-quiz-asked-for-sample-design-choi.md
