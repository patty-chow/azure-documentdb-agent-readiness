---
title: "Readiness checker scores the intentionally-absent local DocumentDB container as a missed accelerator (21 of 100 samples)"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 21
findings: 2
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness checker scores the intentionally-absent local DocumentDB container as a missed accelerator

## What happens today

`loop/run-environment.md` tells every agent, verbatim: "Docker is installed, but no local DocumentDB gateway is running; build and verify against the live cluster instead of a local container." At the same time:

- `prompts/known_accelerators.md` has the row `| Local DocumentDB container | Run the open-source engine locally for tests | github.com/documentdb/documentdb | Docker |`.
- `prompts/readiness_checker.md` (Tools paragraph) says: "Check the known accelerators: anything that exists and would speed this build up but is not installed goes in `accelerators_missed`".
- `factory/tools/environment.py` probes `docker --version` only; nothing in the code-collected inventory says whether a gateway container is running.

So the readiness model is told the container is a known accelerator, is told nothing in the inventory about it, and is told by the environment note that it is deliberately not running. It resolves the contradiction at random: 23 of 120 `02-readiness.json` files (21 of the 100 loop samples, plus two pre-loop `retail-semantic-search` runs) list `ghcr.io/documentdb/documentdb/documentdb-local` / port 10260 in `accelerators_missed`; the other 97 runs, with the identical environment (Docker 29.5.3 present in all 118 Docker-reporting runs, container running in none), do not.

## Why it matters

- The entries are noise in the one field the triage uses to produce "kit-accelerator-missed" findings. Both findings behind this PR (F2854, F2888) were targeted at `Azure/documentdb-agent-kit` with the proposed change "mention it in the kit's setup skill", but the kit already documents the exact command (`README.md` Quickstart step 0 and `skills/local-deployment/SKILL.md`). The gap is in this harness.
- No build was actually affected: in both cited runs the builder never issued `docker run` (the only "docker" hits in `events.jsonl` are the local-deployment skill description), and both builds completed and verified against the live cluster (`03-build.json` status `completed`; the rare-disease run created a `cosmosSearch` vector-diskann index on the M30 cluster). The verdict rule "`ready_with_gaps` ... or accelerators are missing" therefore records a gap the harness itself created.
- Because the inventory does not carry the fact, the signal cannot be audited or reproduced; a rerun of the same sample flips it (e.g. `01-product-catalog-with-vector-search`: flagged in the 20261125 rerun, not in either 20261124 run).

## Proposed change (three small edits, no behaviour change for builders)

1. `prompts/known_accelerators.md` — replace the last row with:

   `| Local DocumentDB container | Run the open-source engine locally for tests (image ghcr.io/documentdb/documentdb/documentdb-local, MongoDB wire protocol on 10260) | github.com/documentdb/documentdb | Docker. Loop runs intentionally do not start it: the environment note names a live cluster to build against. When that note is present, do not list this container in accelerators_missed. |`

2. `prompts/readiness_checker.md` — append to the Tools paragraph, after "...with the install command if you know it from a source.":

   "An accelerator that the shared environment note says is deliberately not provided for this run (for example a local DocumentDB container when a live cluster is the target) is not missed; at most mention it as the `workaround` for the tool it would replace."

3. `factory/tools/environment.py` — add a probe next to `probe_azure_login()`:

   ```python
   def probe_local_gateway() -> dict:
       """Whether a DocumentDB local gateway container is publishing port 10260. Fact, not a model guess."""
       if not shutil.which("docker"):
           return {"name": "local_documentdb_gateway", "state": "docker_absent"}
       done = subprocess.run(["docker", "ps", "--filter", "publish=10260", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=15)
       names = [n for n in done.stdout.split() if n] if done.returncode == 0 else []
       return {"name": "local_documentdb_gateway", "state": "running" if names else "not_running", "containers": names}
   ```

   and in `factory/agents/readiness.py::collect_inventory` add `"local_documentdb_gateway": environment.probe_local_gateway(),` to the inventory dict. The checker is already told to treat the inventory as fact.

## Why not pre-pull and start the container in the build environment

That was the other candidate fix, and I recommend against it as the default:

- It changes what the experiment measures. The point of the loop is agent readiness against Azure DocumentDB (vCore) — the M30 cluster, DiskANN, Entra ID auth, the `mongodb+srv` connection shape. A builder with a local endpoint available may verify there and never touch the service under test; the audit's "verified against the live cluster" signal would weaken for every sample. Feature parity of the OSS local image with the service for `vector-diskann` and Entra ID is not something the kit documents, so it would also need checking first.
- `--parallel 3` runs share one host; a single container on 10260 would need per-run ports plus the TLS/`tlsAllowInvalidCertificates` handling the local-deployment skill describes, for a workflow no run actually tried to use.

If the team does want to measure the kit's local-first workflow, add it as an opt-in arm later: a `--local-gateway` flag in `loop/run_loop.py` that pulls `ghcr.io/documentdb/documentdb/documentdb-local:latest` once, starts one container per run on a free port, and swaps the environment-note sentence for one that names the local URI. That is a separate experiment and a separate PR.

## Evidence (run folders, repo-relative)

- `runs/17-esg-scoring-pipeline/20261124-192259/02-readiness.json` — `accelerators_missed[0]` is the container (sole missed accelerator); `03-build.json` status `completed` against the live cluster; no `docker run` in `events.jsonl`.
- `runs/17-rare-disease-literature-search/20261124-195633/02-readiness.json` — container plus mongosh in `accelerators_missed`; build created a vector-diskann index on the cluster.
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/02-readiness.json` — container is the only missed accelerator.
- `runs/04-natural-language-product-search/20261124-183232/02-readiness.json` — same.
- `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/02-readiness.json` — same.

Counts: 120 `02-readiness.json` files read; `docker` tool `available: true` in 118, absent from the tools list in 2, `available: false` in 0; container named in `accelerators_missed` in 23 files / 22 distinct sample folders (21 of the 100 loop samples). Verdicts: 118 `ready_with_gaps`, 2 `blocked`.

## Verification

**1. Already covered: confirmed (not covered in the target).** The target is the harness, and nothing there already does what the draft asks. `prompts/known_accelerators.md` line 12 still reads `| Local DocumentDB container | Run the open-source engine locally for tests | github.com/documentdb/documentdb | Docker |` and has no carve-out. `prompts/readiness_checker.md` line 22 still says "anything that exists and would speed this build up but is not installed goes in `accelerators_missed`". `factory/tools/environment.py` probes only `docker --version` (line 26), and it has no gateway probe. The kit side is already covered, which is why the theme was moved off `Azure/documentdb-agent-kit`. Kit `README.md` lines 49-51 give `docker run --pull always -dt --name documentdb-local -p 10260:10260 ... ghcr.io/documentdb/documentdb/documentdb-local:latest`, and `skills/local-deployment/SKILL.md` line 11 names the Gateway image on port 10260.

**2. Premise: confirmed.** I checked these claims against the repository and run files:
- `loop/run-environment.md` line 7 contains the quoted sentence ("Docker is installed, but no local DocumentDB gateway is running; build and verify against the live cluster instead of a local container").
- `prompts/readiness_checker.md` line 54 makes "accelerators are missing" a reason for `ready_with_gaps`.
- `factory/tools/environment.py` already imports `shutil` and `subprocess` and defines `probe_azure_login()`.
- `factory/agents/readiness.py::collect_inventory` (line 22) builds the inventory dict that `azure_sign_in` goes into.
- `loop/run_loop.py` has `--parallel`.
- A rescan of `runs/*/*/02-readiness.json` found 120 files. 23 of them name documentdb-local, port 10260 or "local DocumentDB" in `accelerators_missed`, across 22 distinct sample folders. That matches the draft. The draft said "~95" for the other runs, which is now corrected to the exact 97.
- In both finding runs (`17-esg-scoring-pipeline/20261124-192259` and `17-rare-disease-literature-search/20261124-195633`), `events.jsonl` has 0 `docker run` hits, and `03-build.json` for the ESG run has status `completed`.
- The local-gateway facts (image name, port 10260, self-signed TLS that needs `tlsAllowInvalidCertificates`) match the kit's `skills/local-deployment/SKILL.md` lines 11 and 18.
- The draft says nothing about Azure DocumentDB that contradicts the required facts. It calls the target vCore, uses `cosmosSearch` vector-diskann and mentions Entra ID.

**3. Maintainer: confirmed.** As a maintainer of the harness I would accept this PR with small edits. It names exact files and gives the replacement text and code for each. It fixes a real measurement-consistency defect: the environment note and the accelerator list contradict each other, and a fact the model guesses at is not collected by code. It also explains why it rejects the obvious alternative of starting the container. The scope is right: it is the harness, not the kit or the MCP server.

Edits applied:
- Changed "~95" to the exact count of 97.
- Removed the trailing generated-by footer from the body. It belongs on the PR description only when a PR is actually opened.
- Set `sample_count` to the measured 21 loop samples. The theme itself has 2 findings.

## Finding ids

- F2854
- F2888
