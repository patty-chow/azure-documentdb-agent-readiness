---
title: "Readiness stage files ordinary application design choices as learn-docs information gaps; add a builder_decision kind so they go to the decision log instead"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 17
findings: 22
bucket: learn-information_gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness stage files application design choices as learn-docs information gaps

## What happens today

`prompts/readiness_checker.md` asks the readiness checker to "list what the builder will need to know for this sample that no skill, doc or tool answered". `InformationGap` in `factory/models.py` has only `title` and `description`. Then:

- `loop/findings.py` (lines ~100-108) turns **every** `information_gaps` entry into a finding with `target="learn-docs"`, `priority="medium"` and `proposed_change="Document this where the agent looked."`, unconditionally.
- `factory/scoring.py` (line ~107-108) subtracts `GAP_PENALTY` per entry from the readiness score.

With gpt-5-mini the list is dominated by choices the prompt deliberately left to the builder, not missing product facts. Across the 22 findings in this theme (17 distinct samples) the entries are: per-sample document shapes and field names (segments/campaigns, purchase orders, leads/activities, tenants/SKUs, consent records), seed-data contents, counts, licence and PHI-safety wording (regulatory documents, wallet transactions, formulary entries, expense reports, research notes, clinical notes), a risk-scoring formula, which news feed to scrape, a webhook payload and auth scheme, a default consent retention window, REST route and JSON shapes, a CLIP checkpoint and preprocessing, an email/SMS delivery provider, a LangChain agent pattern, and whether agent memory persists across runs.

The model often says so itself. `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json` records: "No skill or doc prescribes a canonical formula; this is a design decision the builder must supply." It is still emitted as a learn-docs gap.

## Why it matters

- **Learn backlog pollution.** The `learn-information_gap` bucket holds 369 findings across all 100 samples. A rough keyword pass over all 120 runs ("builder must choose/pick/invent", "design decision", "unspecified", "prompt leaves X open") matches roughly half of the 461 `information_gaps` entries (250 to 270 depending on the exact pattern, in about 95 samples); treat this as an estimate, not a count. No Learn page for Azure DocumentDB can or should prescribe a sample's field names, seed row count or SMS provider, so a Learn maintainer reading this bucket has to discard most of it by hand before reaching the real gaps (vector index payload shapes, IVF sizing, driver pins) that sit in the same list.
- **Scores are distorted.** Because `scoring.py` penalises every entry, an open-ended prompt scores lower than a tightly specified one even when the service documentation is identical. That makes readiness scores non-comparable across samples.
- **Decisions are recorded in the wrong place.** The pipeline already has the right home for these: the `log_decision` tool with `reason_source="model_default"`, written to `decisions.jsonl` / `04-decisions.md` and reviewed by the auditor. Filing them as information gaps means the auditor sees them twice (once in `<readiness_findings>`, once as decisions) and the decision log review loses the "this was an invented default" signal.

## Proposed change (4 files)

**1. `factory/models.py` — give `InformationGap` a kind.**

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

The default keeps every existing `02-readiness.json` loading unchanged; `_older_files` needs no edit.

**2. `prompts/readiness_checker.md` — replace the Information gaps paragraph.**

> **Information gaps.** List what the builder will need to know for this sample that no skill, doc or tool answered. Set `kind`:
> - `documentation_gap` when the missing item is a fact about Azure DocumentDB, its CLI, SDKs, MCP server or agent kit that a product page or skill could state. Example titles: "IVF parameter sizing", "Driver version support".
> - `builder_decision` when the prompt left an application design choice open and no service documentation could reasonably prescribe it: collection and field names, seed data contents, counts or licence, scoring formulas, which external provider or feed to use, REST route and payload shapes, retention defaults, agent framework or memory patterns. Name the choice in `title` so the builder can log it with `log_decision` (`reason_source: model_default`) when it decides; do not describe it as missing documentation.
>
> Give each a short `title` and a `description` of what is missing and where you looked.

**3. `loop/findings.py` — route by kind.**

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

Add `builder_decision` to the `kind` comment on line 51. Optionally show the kind as a column in the information-gaps table in `factory/reports.py` (line ~123) so `02-readiness.md` readers see the split.

**4. `factory/scoring.py` — penalise only documentation gaps.**

```python
gaps = [g.title or g.description for g in report.information_gaps if g.kind == "documentation_gap"]
```

**Tests.** Extend `tests/test_units.py` with one `ReadinessReport` fixture containing one entry of each kind and assert (a) `findings.py` emits one `learn-docs` and one `sample` finding, (b) the gap penalty counts 1, (c) a legacy entry without `kind` (including the bare-string form already covered at `tests/test_units.py` line ~196) still parses as `documentation_gap`. The existing `InformationGap(title=..., description=...)` constructions in `tests/test_pipeline_offline.py` and `tests/test_units.py` keep working because `kind` has a default.

## Out of scope, noted for the kit maintainers

Several of the 17 samples said the kit's `documentdb-data-modeling` / local-deployment skills "mention sample-data tooling but no canonical dataset". One generic recipe in `skills/data-modeling/SKILL.md` ("synthetic seed data: invent a small deterministic set, tag documents with `seeded: true` and `seed_version`, upsert on a natural key, never commit real PII/PHI") would answer most of the seed-data entries at once. That is an Azure/documentdb-agent-kit change, not a Learn change, and does not replace the pipeline fix above.

## Evidence

- `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json` — "Risk scoring formula and narrative template": the entry itself says it is a design decision the builder must supply.
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json` — "Exact collection schema & field names", "Seed sample data set".
- `runs/11-preference-center-consent-store/20261124-204614/02-readiness.json` — "Retention period policy", "Exact request/response JSON shapes & route names".
- `runs/11-market-news-sentiment-orchestration/20261124-191425/02-readiness.json` — "News source for the scraper", "Notification / webhook schema and authentication".
- `runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json` — "Agent memory persistence requirements".

Other samples in the theme: 08-personalized-email-campaign-builder, 08-regulatory-compliance-rag-checker, 09-clinical-notes-de-identification, 09-crypto-wallet-activity-analyzer, 09-inventory-reorder-multi-agent-system (two runs), 10-drug-formulary-semantic-search, 10-expense-report-auto-categorizer, 10-multi-tenant-storefront-saas, 10-wealth-management-rag-portal, 11-visual-similarity-search-image-embeddings, 12-abandoned-cart-recovery-orchestration, 12-clv-prediction-pipeline.

## Verification

### 1. Already covered? confirmed (not covered)

The pipeline has no way to separate application design choices from documentation gaps today.

- `factory/models.py` line 136: `InformationGap` has only `title` ("A short category, such as 'IVF parameter sizing' or 'Driver version support'") and `description`. There is no kind field.
- `prompts/readiness_checker.md` line 41: "List what the builder will need to know for this sample that no skill, doc or tool answered." It says nothing about design choices or the decision log. A grep for `builder_decision`, "design choice", "design decision", "left open" and `log_decision` in the prompt, models, findings and scoring files finds nothing.
- `loop/findings.py` lines 100-108: every entry becomes `Finding(..., "information_gap", "learn-docs", "medium", ..., proposed_change="Document this where the agent looked.")`, with no condition.
- `factory/scoring.py` lines 107-108: `gaps = [g.title or g.description for g in report.information_gaps]`, and the penalty is `min(len(gaps) * GAP_PENALTY, MAX_GAP_PENALTY)` with `GAP_PENALTY = 2` and `MAX_GAP_PENALTY = 10`.
- The right home already exists: `factory/decision_log.py` (`log_decision` tool, `reason_source`), and `factory/aggregate.py` line 138 reports "Decisions made with no source (`model_default`)".

### 2. Is the premise true? confirmed

- All 22 finding ids are in the `learn-information_gap` bucket (369 findings in total) and come from 17 distinct samples. 09-inventory-reorder-multi-agent-system appears in two runs (20261124-184020 and 20261125-054042).
- The five evidence runs contain the quoted gap titles, word for word. One example: `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json` says "No skill or doc prescribes a canonical formula; this is a design decision the builder must supply."
- There are 120 runs with 461 `information_gaps` entries in total, which matches the draft. The draft gave the keyword-pass figure as exactly 252 entries in 95 samples. A rerun with a similar pattern found 271 entries in 94 samples, so the body now gives that figure as an estimate (correction applied).
- The cited line numbers are correct: models.py 136/157/172, findings.py 51 and 100-108, scoring.py 27-28 and 107-108, auditor.py 137-141 (`<readiness_findings>` includes `information_gaps`). The `_older_files` validator turns string entries into dicts, so a defaulted `kind` loads legacy files with no further change.
- The draft makes no claims about Azure DocumentDB itself, so nothing conflicts with the service facts.

### 3. Maintainer skeptic: confirmed

The draft names four files and gives a concrete schema, prompt text, routing and scoring change, plus tests. It is backward compatible because `kind` has a default. It belongs in the harness repository (abinav2307/azure-documentdb-agent-readiness), not in Learn, the kit or the MCP server. The optional seed-data recipe is correctly marked as a separate Azure/documentdb-agent-kit item. I would accept it after two small edits, both now applied: softening the keyword-pass count, and noting the existing test fixtures and the reports.py table.

## Finding ids

- F1310
- F1348
- F1382
- F1413
- F1443
- F1445
- F1500
- F1535
- F1536
- F1600
- F1636
- F1665
- F1731
- F1803
- F1839
- F1840
- F1870
- F1871
- F1902
- F1962
- F1996
- F2097
