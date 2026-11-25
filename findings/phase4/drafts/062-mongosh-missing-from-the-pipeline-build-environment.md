---
title: "Add mongosh to the harness prerequisites (missing in 120/120 run inventories)"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
priority: P1
sample_count: 19
findings: 3
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add mongosh to the harness prerequisites (it is probed and allowlisted but never installed)

## What happens today

`factory/tools/environment.py` probes `mongosh` ("Check connectivity and indexes by hand") and `factory/config.py` / `.env.example` include `mongosh` in `FACTORY_ALLOWED_COMMANDS`, so the harness clearly intends the builder to have it. But the setup steps in `loop/README.md` (az login, provision, `npx skills add`, `pip install`, `python main.py check`) never say to install it, and nothing in the repo installs it.

In the 2026-11-24/25 sweep over the 100 sample prompts:

- `02-inventory.json` reports `mongosh ... "available": false, "detail": "not found on PATH"` in **120 of 120** run folders.
- The readiness agent listed mongosh under `accelerators_missed` in **19 runs (19 distinct samples)**, e.g. "mongosh (shell) is not on PATH - install via package manager (e.g., npm i -g mongosh ...)".
- Every one of those readiness reports also emits an `inventory_recommendations` entry `{"name": "mongosh", "worth_adding": true, ...}`, so the same recommendation is regenerated on every run instead of being acted on once.

## Why it matters

- The builder could not do interactive checks of collections, indexes or inserted data. It compensated with PyMongo helper scripts (17-rare-disease-literature-search) or the DocumentDB MCP server's `list_indexes` / `find_documents` tools (17-stress-testing-multi-agent-runner, 19-proactive-outreach-orchestration), and in one build wrote "mongosh is not available in the environment ... install mongosh locally" into the generated README (`03-build.md`, 19-proactive-outreach-orchestration).
- The Agent Kit's `query-optimizer` skill gives mongosh and MCP as parallel paths (`db.<coll>.getIndexes()`, `.explain("executionStats")`, `$indexStats`, and a whole "Local mongosh Commands (No MCP Required)" section). With mongosh absent, the experiment can only ever measure the MCP path, so it cannot tell whether the kit's mongosh guidance is correct or whether an agent without the MCP server would succeed.
- The constant "mongosh missing" entries inflate the `accelerators_missed` metric with a harness artifact rather than a kit or docs gap.

## Proposed change (small PR)

1. **`loop/README.md`**, setup list: add a step after the skills install

   > 4. Install the MongoDB Shell so the builder can inspect collections and indexes by hand: `npm i -g mongosh` (or `brew install mongosh`). The DocumentDB MCP server covers the same checks, but the Agent Kit skills show mongosh commands and the readiness stage flags it when it is missing.

   and amend the `python main.py check` line to "should show `az login` ok, `mongosh` ok, 17 skills, and all three MCP servers ok."

2. **`main.py` `check` command** (around line 120, where `environment.probe_clis()` results are printed): when `c.name == "mongosh"` and `not c.available`, append a hint such as `install with: npm i -g mongosh` so the operator sees the fix in the same output the readiness agent reads.

No Dockerfile or build image exists in this repo (the inventories show Apple Git on the operator's machine), so the host prerequisite is the right place; if a container image is added later, the same `npm i -g mongosh` belongs there.

The companion kit-side gap (the Agent Kit never listing mongosh as a required tool in a setup skill) is tracked separately under the agent-kit mongosh theme; this PR only fixes the harness.

## Evidence (run folders)

- `runs/17-rare-disease-literature-search/20261124-195633/02-readiness.json` (`accelerators_missed`, `inventory_recommendations`)
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json` (`accelerators_missed`: azd, bicep, terraform, mongosh, dotnet)
- `runs/19-proactive-outreach-orchestration/20261124-205844/02-readiness.json` and `03-build.md` line 44 (builder tells users to install mongosh themselves)
- `runs/17-rare-disease-literature-search/20261124-195633/02-inventory.json` (`command_line_tools` -> mongosh not found on PATH; same in all 120 inventories)
- Harness source: `factory/tools/environment.py` (CLI_PROBES), `factory/config.py` (DEFAULT_ALLOWED_COMMANDS), `loop/README.md` (setup steps)

## Verification

### 1. Already covered? — confirmed (not covered)
The harness expects mongosh but never installs or documents it:
- `factory/tools/environment.py:27`: `"mongosh": (["--version"], "Check connectivity and indexes by hand")`
- `factory/config.py:16` and `.env.example:31` list `mongosh` in the allowed commands.
- `loop/README.md` setup steps 1-5 (lines 29-36) cover `az login`, `loop/provision.sh`, `npx skills add Azure/documentdb-agent-kit`, `pip install ...`, and `python main.py check`. None of them mentions installing mongosh. The repo has no Dockerfile or build image (`find . -name "Dockerfile*"` outside runs/ returns nothing).
- `main.py:120-121` prints `ok`/`NO` for each CLI probe and gives no install hint.

### 2. Is the premise true? — confirmed
- All 120 `runs/*/*/02-inventory.json` files mention mongosh, and all 120 report it as "not found on PATH" (counted with a script).
- 19 `02-readiness.json` files from 19 distinct sample slugs list mongosh under `accelerators_missed`.
- `runs/19-proactive-outreach-orchestration/20261124-205844/03-build.md` line 44 says that mongosh is not available in the environment and tells users to install it locally or use the documentdb MCP server tools.
- Agent Kit `skills/query-optimizer/SKILL.md` lines 33-51 pair each MCP tool with a mongosh command (`db.<coll>.getIndexes()`, `.explain("executionStats")`, `$indexStats`, `db.currentOp()`). Line 69 starts the section "Local mongosh Commands (No MCP Required)".
- mongosh is published on npm (`npm i -g mongosh`) and Homebrew (`brew install mongosh`). Azure DocumentDB supports MongoDB-wire-protocol clients, mongosh included, over the documented `mongodb+srv://...mongocluster.cosmos.azure.com` connection string with TLS and SCRAM-SHA-256. The draft makes no claims about the service that go against the facts given for this stage.

### 3. Maintainer skeptic — confirmed
This is the correct repository (the harness). The PR names exact files (`loop/README.md` setup list, `main.py` check output near line 120) and gives a concrete, small change. It has a DocumentDB angle: without the shell, the experiment can only test the MCP half of the Agent Kit's query-optimizer guidance, and the missing shell adds harness noise to the `accelerators_missed` metric. I would accept it as written.

No corrections were needed. Priority is P1 because 19 distinct samples were affected (10 or more), and every one of the 120 run inventories shows the gap. No build was blocked, since builders fell back to PyMongo or the MCP server.

## Finding ids

- F2889
- F2957
- F3335
