# Azure DocumentDB agent readiness: the 100-sample run

This branch (`samples-loop`) is a fork of
[abinav2307/azure-documentdb-agent-readiness](https://github.com/abinav2307/azure-documentdb-agent-readiness),
a five-stage pipeline that measures how ready an AI coding agent is to build an application on
Azure DocumentDB. The fork adds a loop that ran the pipeline over 100 starter prompts, the complete
results, and a triage of what the runs found into filing-ready issues and pull requests for the
Agent Kit, the DocumentDB MCP server and Microsoft Learn.

## The pipeline (unchanged from upstream, one deviation)

`main.py run <prompt>` takes a starter prompt and runs five stages with one model:

1. Prompt review: is the prompt sufficient to build from?
2. Readiness: a cold quiz of 15 fixed and 5 sample-specific questions answered from memory, then
   checked against public sources, giving a confidence score out of 100.
3. Build: the agent builds the sample, with the Agent Kit skills and the DocumentDB, Azure and
   Learn MCP servers available.
4. Decision log.
5. Audit: the build is scored against hidden reference requirements and best practices, and
   documentation gaps are recorded.

The fork changes one line of the pipeline: `factory/llm.py` raises Agent Framework's
`max_consecutive_errors_per_request` from 3 to 10 (see `loop/README.md`, Deviations).

## What this fork adds

| Path | What it is |
| --- | --- |
| `loop/` | The queue runner and everything around it: per-run environment note and virtual environment, auto-resume, database cleanup, commit-and-push per run, experiment arms, reports. `loop/README.md` documents it. |
| `samples/` | The 100 starter prompts, 20 per vertical (retail, fintech, healthcare, banking, customer-360), imported from the samples spreadsheet, plus `samples/index.json`. |
| `requirements/` | One reference requirements file per sample, drafted with the model, then reviewed and rewritten by two review workflows (`requirements/REVIEW.md`). |
| `runs/` | Every run folder, including the generated applications, and `runs/loop-state.json` with every run's outcome. `runs/gallery-insights.md` is the pipeline's own roll-up over the default arm. |
| `findings/` | `TRIAGE.md` and `findings.jsonl` (every finding extracted from the runs, grouped by where the fix belongs), `PHASE-REPORT.md` (default arm) and `PHASE-REPORT-control.md`. |
| `findings/phase4/` | The triage into filing-ready items: `FILINGS.md` (index), `filings/` (43 items), `drafts/` (the 135 drafts they were consolidated from), `SME-QUESTIONS.md`, `DECISIONS.md`, `REVIEW.md`. |

## How the experiment ran

- Model: gpt-5-mini on Azure OpenAI, Entra-only, 500K tokens per minute. One shared M30
  DocumentDB cluster; each run used its own database, dropped afterwards. Both resources were
  deleted when the experiment ended (`loop/teardown.sh`); `loop/provision.sh` recreates them.
- Phase 1: prompt review and readiness for all 100 samples.
- Phase 2: build and audit, resuming each phase-1 run folder.
- Phase 3: reruns of five samples hit by a harness defect, a control arm (no Agent Kit skills, no
  MCP servers) on two samples per vertical, and the roll-up.
- Phase 4: findings triage. Two Claude workflows clustered 3,528 default-arm findings into 135
  themes, drafted one issue or PR per theme, verified each draft three ways (already covered?
  premise true? would the maintainer accept?), then consolidated overlapping drafts into 43 filings
  and checked each merge. Nothing has been filed anywhere.

## Headline results (default arm, 100 samples)

| Measure | Result |
| --- | --- |
| Readiness confidence, median (range) | 72 (51 to 81) |
| Builds completed / partial | 71 / 29 |
| Audit passed with findings / failed | 97 / 3 |
| Blocked by the prompt | 1 (requires BSON binary vectors, which the service does not index) |
| Cold-quiz questions wrong in nearly every run | CLI command group, Bicep and Terraform resource types, connection string format, Entra ID authentication, local development image, resource provider type |

Control arm, same ten samples: readiness confidence averaged about 40 without the kit and MCP
servers against about 73 with them. Builds completed and audits passed in both arms.

The cold-quiz pattern is consistent: the model's prior knowledge comes from Azure Cosmos DB for
MongoDB (request units) and MongoDB Atlas. Grounding in Learn and the Agent Kit corrects it in
every run, which is why most of the proposed fixes target discoverability and consistency rather
than missing features.

## What the triage proposes

43 filing-ready items in `findings/phase4/filings/`, indexed in `findings/phase4/FILINGS.md`:
18 pull requests for the Agent Kit (one per skill or cross-cutting change), 11 Learn feedback items,
1 item for the DocumentDB MCP server, 1 for the Azure CLI extension, and 12 for the pipeline itself
(on hold). The five P0 items: the kit's connection-string files contradict the published string
(retryWrites, host suffix, CLI spelling); 85 of 100 builds fell back to `az cosmosdb` because no
skill names the documentdb CLI extension; the MCP server's gated-tool refusals are not actionable for
an agent; and two harness defects that inflated the sample counts.

Many items carried questions only the service team can answer. `findings/phase4/SME-QUESTIONS.md`
lists them by topic; `findings/phase4/DECISIONS.md` records each one that has since been settled
from primary sources, with the exact pages, issues and files, and what remains open.

Counts in every filing come from this single run, whose harness had defects that are now identified
(MCP management and write tools left off, the installed kit reported as missing, empty builds graded).
They should be re-measured after those fixes before being quoted outside the team.

## Reproducing

```
az login
loop/provision.sh                                   # Azure OpenAI + M30 cluster, prints .env values
cp .env.example .env                                # fill in the printed values
npx skills add Azure/documentdb-agent-kit
pip install -r requirements.txt -r loop/requirements-loop.txt
python main.py check
python loop/run_loop.py --stop-after readiness --parallel 3     # phase 1
python loop/run_loop.py --parallel 3                            # phase 2
loop/phase3.sh 3                                                # phase 3
```

`loop/README.md` has the full operating notes: state, arms, auto-resume, database cleanup, costs.

## Credits

The pipeline is Abinav Rameesh's (`abinav2307`). The loop, the sample import, the requirements
drafting and review, and the phase-4 triage were built on this fork with Claude Code.
