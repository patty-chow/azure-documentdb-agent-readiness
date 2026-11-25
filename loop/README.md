# Samples loop

Runs the five-stage readiness pipeline in this repository over the 100 starter prompts in
`samples/`, one run per sample, and collects what each run found into a triage file for the
product team. The pipeline itself is unchanged; the loop only queues it, keeps state, and
reads the run folders.

```
samples/index.json        100 samples: id, vertical, title, agent type, concepts, description, prompt path
samples/<vertical>/*.md   the starter prompts, one file each (what `main.py run` takes)
loop/import_samples.py    regenerates both from the Azure DocumentDB Samples spreadsheet
loop/run_loop.py          the queue runner
loop/findings.py          run folder -> findings; builds findings/TRIAGE.md
loop/arms/                skill and MCP configurations for the experiment arms
loop/provision.sh         creates the Azure resources once; loop/teardown.sh deletes them
runs/loop-state.json      what has run, exit codes, verdicts, minutes, run folder
runs/_loop_logs/          console output of every run
findings/TRIAGE.md        grouped findings by target repository, plus MCP usage per run
findings/findings.jsonl   the same, one JSON object per finding
```

## One-time setup

1. `az login`, then `loop/provision.sh`. It creates an Entra-only Azure OpenAI account with a
   gpt-5-mini deployment, grants you the OpenAI User role, creates one M30 DocumentDB cluster
   (DiskANN needs M30 or higher), opens its firewall to this machine, and prints the `.env` lines.
2. Copy `.env.example` to `.env` and fill in the printed values. Leave `AZURE_OPENAI_API_KEY`
   empty so the Azure CLI credential is used.
3. Install the Agent Kit skills into `.agents/skills`: `npx skills add Azure/documentdb-agent-kit`.
4. `python main.py check` should show `az login` ok, 17 skills, and all three MCP servers ok.

## Running

```
python loop/run_loop.py --dry-run                       # the queue
python loop/run_loop.py --ids retail-01 --stop-after readiness   # a cheap first run
python loop/run_loop.py --vertical retail --parallel 3  # one vertical
python loop/run_loop.py --parallel 3                    # everything not yet finished
python loop/run_loop.py --triage-only                   # rebuild findings/ from existing runs
```

A full run (review, readiness, build, audit) took about two hours in the committed example, so
run several at a time. The gpt-5-mini deployment has 500K tokens per minute; three parallel runs
have stayed well inside that. Runs are resumable at the pipeline level too: a failed run prints
a `--resume` command, and `--rerun` in the loop starts a fresh run for a sample.

### Experiment arms

`--arm` picks the condition. The default is the Agent Kit plus all three MCP servers, which is
the arm the 100-sample experiment uses. `control` (no skills, no MCP servers), `kit-only` and
`mcps-only` exist for ablations on prompts where the default arm got confused. State is kept per
arm, so the same sample can run under several.

### Letting the builder provision Azure resources

By default the builder may only run read-only `az` and `azd` commands and uses the shared
cluster from `DOCUMENTDB_URI`. For prompts where provisioning behaviour is the thing being
measured:

```
python loop/run_loop.py --ids retail-05 --allow-azure-writes --cleanup
```

`--cleanup` lists the resource group before the run and deletes anything new afterwards, except
the shared cluster and the Azure OpenAI account. Write-enabled runs with cleanup go one at a time.

## Findings

Every run appends to `findings/`. The triage file groups findings by where the fix belongs:

| Target | Repository |
|---|---|
| agent-kit | Azure/documentdb-agent-kit |
| documentdb-mcp | microsoft/documentdb-mcp |
| learn-docs | Azure DocumentDB pages on Microsoft Learn |
| sample | the generated app or the starter prompt itself |

Sources, per run folder: audit `doc_gaps`, readiness confusions that were not `correct`,
information gaps, missed accelerators, violated practices, and requirement misses caused by a
silent skill or a missing tool. The last section counts tool calls per MCP server from
`events.jsonl`, so a run that never touched the DocumentDB or Azure server is visible at a glance.

Nothing is filed anywhere automatically. Pick rows from the triage file and open the PRs by hand.

## Costs and clean-up

The M30 cluster bills while it exists, roughly $200 a month. `loop/teardown.sh` deletes the
cluster and the Azure OpenAI account (and purges it) and anything tagged `purpose=samples-factory`.
