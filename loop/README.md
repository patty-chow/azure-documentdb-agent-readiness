# Samples loop

Runs the five-stage readiness pipeline in this repository over the 100 starter prompts in
`samples/`, one run per sample, and collects what each run found into a triage file for the
product team. The pipeline itself is unchanged; the loop queues it, prepares the environment
each run needs, keeps state, and reads the run folders.

```
samples/index.json          100 samples: id, vertical, title, agent type, concepts, description, prompt path
samples/<vertical>/*.md     the starter prompts, one file each (what `main.py run` takes)
requirements/<stem>.md      reference requirements per sample, hidden from the builder, scored by the audit
loop/import_samples.py      regenerates samples/ from the Azure DocumentDB Samples spreadsheet
loop/draft_requirements.py  drafts the missing requirements files with the model, for a person to review
loop/run_loop.py            the queue runner
loop/run-environment.md     what every agent is told about the live cluster (rendered per run)
loop/findings.py            run folder -> findings; builds findings/TRIAGE.md
loop/arms/                  skill and MCP configurations for the experiment arms
loop/provision.sh           creates the Azure resources once; loop/teardown.sh deletes them
runs/loop-state.json        every run: sample, arm, run folder, exit code, how far it went, verdicts, minutes
runs/_loop_logs/            console output of every run and the rendered environment notes (not in git)
findings/TRIAGE.md          grouped findings by target repository, plus MCP usage per run
findings/findings.jsonl     the same, one JSON object per finding
```

## One-time setup

1. `az login`, then `loop/provision.sh`. It creates an Entra-only Azure OpenAI account with a
   gpt-5-mini deployment, grants you the OpenAI User role, creates one M30 DocumentDB cluster
   (DiskANN needs M30 or higher), opens its firewall to this machine, and prints the `.env` lines.
2. Copy `.env.example` to `.env` and fill in the printed values. Leave `AZURE_OPENAI_API_KEY`
   empty so the Azure CLI credential is used.
3. Install the Agent Kit skills into `.agents/skills`: `npx skills add Azure/documentdb-agent-kit`.
4. `pip install -r requirements.txt -r loop/requirements-loop.txt` in a virtual environment.
5. `python main.py check` should show `az login` ok, 17 skills, and all three MCP servers ok.
6. `python loop/draft_requirements.py` drafts a requirements file for every sample that has none.
   Skim them; the audit scores each build against them.

## Running in two phases

```
python loop/run_loop.py --dry-run                              # the queue
python loop/run_loop.py --stop-after readiness --parallel 3    # phase 1: review + readiness, all samples
python loop/run_loop.py --parallel 3                           # phase 2: resume each run through build + audit
python loop/run_loop.py --arm control --stop-after readiness --ids retail-01 retail-11 fintech-01 fintech-11 \
    healthcare-01 healthcare-11 banking-01 banking-11 customer-360-01 customer-360-11
                                                                # control arm on two samples per vertical
python loop/run_loop.py --triage-only                          # rebuild findings/ from existing runs
```

Phase 1 takes about 11 minutes per sample with gpt-5-mini and yields the prompt-review verdict,
the cold-quiz confusions and the readiness confidence score without building anything. Phase 2
resumes each phase-1 run folder, so review and readiness are not repeated. A full run takes
roughly 11 to 15 minutes. The deployment has 500K tokens per minute; three parallel runs stay
well inside that.

State decides what runs. A sample is complete for a requested stop point when an earlier run
with exit code 0 reached at least that far; a partial run is resumed from its folder;
`--rerun` forces a fresh run. The loop exits with `PHASE DONE` when the queue is finished and
with `STUCK` after three consecutive failures.

### What the loop does around each pipeline run

- **Environment note.** `loop/run-environment.md`, rendered with the sample's database name, is
  passed as the pipeline's shared context (`--skill`). It tells the agents a live cluster is
  reachable through `DOCUMENTDB_URI`, which database to use, that the DocumentDB MCP points at
  the same cluster, and never to write the connection string into a file. Without it the builder
  targets a local Docker gateway and never touches the MCP. `--no-env-note` turns it off.
- **Virtual environment.** Each run gets its own venv on `PATH`, so the builder's `pip install`
  works on a Mac whose system Python refuses it. Deleted after the run. `--no-venv` turns it off.
- **Insufficient prompts.** `--force` is on by default: the pipeline builds on the reviewer's
  assumptions, and the review verdict is recorded in state. `--no-force` stops at the gate instead.
- **Database hygiene.** Databases the run created on the shared cluster are dropped afterwards
  (admin, config and local are never touched) and listed in state. `--keep-databases` turns it off.
- **Auto-resume.** A model or network failure (exit code 7) is retried once with `--resume`.
- **Commit and push.** After each run the run folder, `runs/loop-state.json` and `findings/` are
  committed and pushed. Any staged file containing the cluster password is removed from the
  commit and reported. `--no-push` and `--no-commit` are available.
- **Stay awake.** The loop holds a `caffeinate` assertion while it runs.
- **Several model deployments.** The Azure OpenAI quota is per region. With `FACTORY_OPENAI_ENDPOINTS`
  set in `.env` to a comma-separated list of endpoints (one gpt-5-mini deployment per region, made
  with the same template), runs rotate through them and `--parallel` can go up by the same factor.
  The endpoint each run used is recorded in state.
- **Azure writes.** `--allow-azure-writes --cleanup` lets the builder provision; the resource group
  is compared before and after and anything new is deleted, except the shared cluster and the
  Azure OpenAI account. Such runs go one at a time.

### Experiment arms

`--arm` picks the condition. `default` is the Agent Kit plus all three MCP servers, the arm the
100-sample experiment uses. `control` (no skills, no MCP servers) runs on two samples per vertical
for comparison; `kit-only` and `mcps-only` exist for ablations. State is kept per arm. The
environment note omits the MCP sentence for arms without the DocumentDB server.

## Findings

Every run appends to `findings/`. The triage file groups findings by where the fix belongs:

| Target | Repository |
|---|---|
| agent-kit | Azure/documentdb-agent-kit |
| documentdb-mcp | microsoft/documentdb-mcp |
| learn-docs | Azure DocumentDB pages on Microsoft Learn |
| sample | the generated app or the starter prompt itself |

Sources, per run folder: audit `doc_gaps`, readiness confusions that were not `correct`,
information gaps, missed accelerators, violated practices, requirement misses caused by a silent
skill or a missing tool, and a build that made no DocumentDB MCP call although the server was
available. The last section counts tool calls per MCP server from `events.jsonl`.

Nothing is filed anywhere automatically. Pick rows from the triage file and open the PRs by hand.

## Deviations from the upstream pipeline

The fork changes one line of the pipeline itself. `factory/llm.py` sets Agent Framework's
`max_consecutive_errors_per_request` to 10 (the library default is 3). With gpt-5-mini, 4 of the
first 25 builds called the `log_decision` tool with invalid arguments three times in a row, which
made the framework refuse every further tool call for that request; the builder then returned a
partial build and the audit failed it. Runs before 2026-11-24 23:10 (retail-07, retail-09,
retail-13, retail-19) were affected and were rerun afterwards. Everything else in `factory/` is
upstream as committed.

## Costs and clean-up

The M30 cluster bills while it exists, roughly $200 a month. `loop/teardown.sh` deletes the
cluster and the Azure OpenAI account (and purges it) and anything tagged `purpose=samples-factory`.
