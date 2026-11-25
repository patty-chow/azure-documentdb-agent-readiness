---
title: "Build prompt and audit stage: require language-aware pins + lockfile, exhaustive valid .env.example, offline test target, runtime version, Clean-up/Testing README sections"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 18
findings: 25
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Build prompt and audit stage: require language-aware pins + lockfile, exhaustive valid `.env.example`, offline test target, runtime version, Clean-up/Testing README sections

## What happens today

`prompts/builder.md` asks for only two hygiene deliverables: "ship a `.env.example` with placeholder values" and a README that covers "how to clean up". The team checklist (`best-practices/checklist.md`) already states the intent in general terms: "A `.env.example` (or equivalent) lists every required setting with placeholder values" (Authentication and secrets), "Clean-up steps are provided" (Provisioning), and under "Sample hygiene" "Dependencies are pinned" and "Tests exist and pass without a live cloud resource, or the README says what they need". But those rules are not carried into the build prompt, are not language-aware, and are not checked mechanically by the auditor. The shared gallery-hygiene block in `requirements/retail-semantic-search.md` (line 29), which `loop/draft_requirements.py` appends to every generated requirements file (101 files), says:

> Dependencies are pinned in `requirements.txt`.

Nothing in the build prompt tells the builder which variables belong in `.env.example`, what "pinned" means per language, which runtime the sample was tested on, or that the README needs a Testing section distinguishing offline from live tests. The auditor then files each omission as a Learn documentation gap (`learn_doc` / `discoverability`), which sends product-doc work to the wrong team.

A static scan of the latest run of each of the 101 samples (`runs/<slug>/<latest>/app`) shows:

| Defect | Samples |
|---|---|
| `.env.example` omits a variable the code reads (`process.env.X` / `os.environ[...]`), e.g. `PORT`, `MAX_POOL_SIZE`, `DATABASE_NAME`, `OPENAI_CHAT_MODEL` | 43 |
| `.env.example` malformed (unbalanced quote on a value line) | 3 |
| Python `requirements.txt` with floating `>=` / unpinned names | 38 |
| Node sample with no `package-lock.json` / `npm-shrinkwrap.json` | 2 |
| README with no Clean-up / teardown section | 58 |
| No `tests/` folder or test files at all | 35 to 40 (depends on which test-file name patterns are counted) |

## Why it matters

25 audit findings across 18 of the 100 samples were filed against Learn for this; all are harness defects. Concrete cost in the runs:

- **Wrong failure on a correct sample.** `06-omnichannel-interaction-history` (Node + Mongoose) committed `package-lock.json`, yet the audit marked "Dependencies are pinned in `requirements.txt`" as `partly_met`, cause `prompt_silent`, because the requirement names a Python file.
- **Broken copy-paste.** `13-basel-iii-capital-ratio-calculator/app/.env.example` has `DOCUMENTDB_URI="<...placeholder...>` with no closing quote; a newcomer copying it gets an immediate parse error.
- **Tests never ran.** `19-option-chain-data-store` pinned `pydantic==1.10.12` and `fastapi==0.95.2`, README says "Python 3.10+", the runner had Python 3.13; the build report records that pytest could not be executed, so the sample shipped unverified.
- **Feature dropped under resolver pressure.** `20-provider-directory-semantic-search` rewrote `requirements.txt` four times (`llama-index` 0.10.0 → 0.14.26, `fastapi` → 0.100.1, `openai` → 1.8.0) then removed LlamaIndex from the runtime entirely, although the prompt asked for a LlamaIndex service. A required "optional extras are pinned and install-tested" rule would have kept it.
- **No offline target.** `02-real-time-event-stream-ingestion`, `02-transaction-categorization-agent`, `20-store-locator-with-geospatial-search` ship no tests runnable without the cluster; `20-identity-resolution-multi-agent` has unit tests but the README never says which tests need `DOCUMENTDB_URI` or how to remove seeded data.

## Proposed change

### 1. `prompts/builder.md` — add after "How to work", before "Limits"

```markdown
## Deliverables every sample ships

Reviewers check these mechanically; a sample that misses one is sent back.

- **`.env.example`**, syntactically valid (every value quoted or unquoted consistently, no
  unbalanced quotes). It lists **every** environment variable any file in the sample reads
  (`process.env.X`, `os.environ[...]`, `os.getenv`), required ones first, each with a one-line
  comment saying what it does and a placeholder value only (`<your-cluster-name>`, never a real
  host, user or key). Include the line
  `# Get the connection string with: az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <resource-group>`
  and `# Copy to .env; never commit .env`.
- **Exact pins and a committed lockfile for the sample's language.**
  Python: `requirements.txt` with `==` for every package (or `pyproject.toml` plus a committed
  `poetry.lock` / `uv.lock` / `constraints.txt`). Node: exact versions in `package.json` and a
  committed `package-lock.json` or `npm-shrinkwrap.json`. Optional integrations (LlamaIndex,
  LangChain, Beanie, ...) go in their own pinned block (`requirements-extras.txt` or an npm
  optional group) that you install once and record as `verification_done`; do not drop a
  framework the prompt asked for because the resolver failed, pin a working set instead.
- **Tested runtime.** The README states "Tested with Python 3.11" (or the Node major) and the
  `engines` field / `requires-python` says the same. Use the runtime the run environment
  provides and pin packages that support it.
- **Tests that run offline.** A `tests/` folder with fixtures (mongomock, mongodb-memory-server,
  or driver mocks; a stubbed embedding client). These emulators do not implement Azure DocumentDB
  `cosmosSearch` vector or `$search` text queries, so stub those calls at the data-access layer
  rather than expecting the emulator to run them and a `test:unit` / `pytest -m "not live"`
  target that passes with no `.env`. Live tests are marked and skipped when `DOCUMENTDB_URI`
  is unset.
- **Seed script** that batches writes (`insert_many` / `bulk_write`, bounded batch size), is
  idempotent (upsert on a deterministic key), and takes `--force` to drop and reseed. A
  `sample-data.md` documents the seed document shape and any fixed taxonomy the sample uses.
- **README sections**, in this order: What this sample shows, Prerequisites, Setup (including
  `.env.example` → `.env`), Run, **Testing** (which tests are offline, which need the cluster
  and an API key, and the commands for each), **Clean-up** (commands to drop the sample
  database or collections, and to delete any Azure resources the IaC created).
```

### 2. `best-practices/checklist.md` — replace the five-bullet "Sample hygiene" section (and tighten the existing `.env.example` bullet under "Authentication and secrets" rather than duplicating it)

Under "Authentication and secrets", change the existing bullet to: "A syntactically valid `.env.example` names every environment variable the code reads, with a one-line comment and a placeholder value each."

```markdown
## Sample hygiene

- The README has What-it-shows, Prerequisites, Setup, Run, Testing and Clean-up sections, and states the Python or Node version the sample was tested with.
- The sample runs with the commands in the README on that version.
- Dependencies are pinned for the sample's language: Python has `==` pins or a committed lockfile/constraints file; Node has a committed `package-lock.json` or `npm-shrinkwrap.json`. Optional extras are pinned and install-tested separately.
- Unit tests run and pass with no `.env` and no live cluster; tests that need the cluster are marked and skipped when `DOCUMENTDB_URI` is unset.
- The seed script is batched, idempotent, and documents its document shape.
- The sample names the service correctly and does not use a former or neighbouring product name.
```

### 3. Shared requirements block — `requirements/retail-semantic-search.md` line 29, then regenerate or `sed` the 101 generated files

```markdown
- Dependencies are pinned for the sample's language (Python: exact versions in `requirements.txt` or a committed lockfile/constraints file; Node: a committed `package-lock.json` or `npm-shrinkwrap.json`).
- `.env.example` names every environment variable the code reads, with a placeholder and a comment each.
- The README has Testing and Clean-up sections and states the tested Python or Node version.
```

(`loop/draft_requirements.py` reads this section from the example file at `EXAMPLE = REQUIREMENTS / "retail-semantic-search.md"`, so one edit plus a re-run of the appender fixes all 101 files.)

### 4. `prompts/auditor.md` — add after "Step 2: check the app against each practice"

```markdown
**Hygiene checks are judged against the sample's own language and files, not against a
Python template.** For dependency pinning, look for `==` pins or a committed lockfile when the
sample is Python, and for a committed `package-lock.json` or `npm-shrinkwrap.json` when it is
Node; a Node sample is not marked down for lacking `requirements.txt`. For `.env.example`, list
the variables the code reads (`process.env.X`, `os.environ[...]`, `os.getenv`) and name each one
missing from the file, and flag any line with an unbalanced quote. For the README, confirm the
Testing and Clean-up headings exist and a tested runtime version is stated. A failure of any of
these is a `builder_error` with a prompt or checklist fix; it is never a `learn_doc` or
`discoverability` gap, because the product documentation is not where sample scaffolding rules
belong.
```

### 5. Optional: a deterministic pre-audit lint

A 60-line `factory/tools/hygiene_lint.py` run before the auditor (env-var diff, quote balance, pin regex per language, README heading check, lockfile presence) would make these checks independent of the model and give the auditor a ready-made evidence list. Happy to add it in a follow-up if the prompt changes alone are preferred first.

## Evidence

- `runs/06-omnichannel-interaction-history/20261124-204007/05-audit.json` — Node sample with `package-lock.json` marked `partly_met` on "Dependencies are pinned in `requirements.txt`"
- `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/app/.env.example` — unbalanced quote on the `DOCUMENTDB_URI` placeholder line
- `runs/19-option-chain-data-store/20261124-192712/03-build.json` — pytest not run: pydantic 1.x pinned, runner on Python 3.13, no tested-version statement
- `runs/20-provider-directory-semantic-search/20261124-200008/events.jsonl` — four `requirements.txt` rewrites, then LlamaIndex removed from the runtime
- `runs/20-identity-resolution-multi-agent/20261124-210002/doc-gaps.md` — floating `>=` pins; README lacks Clean-up and a unit-vs-integration run matrix

Related findings on the same theme: F0271, F0276, F0334, F0336, F0337, F0443, F0444, F0445, F0515, F0542, F0903, F0933, F0986, F2171, F2229, F3196, F3247, F3313, F3341, F3381, F3383, F3406, F3448, F3482, F3516 (18 distinct samples). After this lands, those 25 Learn-targeted findings should be reclassified to target `pipeline` and closed.

## Verification

### 1. Already covered? — partially_covered

The pipeline repo already states part of the intent, but only as general checklist bullets that the build prompt does not carry and the auditor does not check per language:

- `best-practices/checklist.md` line 28: "A `.env.example` (or equivalent) lists every required setting with placeholder values." Line 52: "Clean-up steps are provided." Lines 56-59 (Sample hygiene): README with clean-up steps, "Tests exist and pass without a live cloud resource, or the README says what they need", "Dependencies are pinned."
- `prompts/builder.md` line 29 asks for a README covering "how to clean up", and line 35 asks to "ship a `.env.example` with placeholder values". There is nothing about every variable the code reads, syntax validity, lockfiles per language, a tested runtime, an offline test target or a Testing section.
- `requirements/retail-semantic-search.md` line 29: "Dependencies are pinned in `requirements.txt`." `loop/draft_requirements.py` (`EXAMPLE = REQUIREMENTS / "retail-semantic-search.md"`, `gallery_section()`) copies this into the generated files. All 101 files under `requirements/` contain it.
- `prompts/auditor.md` has no language-aware hygiene paragraph. "Step 2: check the app against each practice" is at line 64.
- The agent kit has generic `.env.example` guidance (`skills/local-deployment/local-env-driven-config.md` lines 48-75: "commit `.env.example`") but nothing on lockfiles or offline tests. In any case, that is not the target here.

Correction applied: the body now says that the checklist already covers `.env.example` and clean-up in general terms. It now speaks of the five-bullet Sample hygiene section, not "four one-liners". It now tightens the existing `.env.example` bullet instead of adding a duplicate.

### 2. Is the premise true? — confirmed (minor corrections applied)

- Run evidence checked:
  - `runs/06-omnichannel-interaction-history/20261124-204007/05-audit.json`: requirement "Dependencies are pinned in requirements.txt." is `partly_met`, cause `prompt_silent`, and the evidence says package-lock.json is present.
  - `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/app/.env.example`: line 2 has an unbalanced quote.
  - `runs/19-option-chain-data-store/20261124-192712/03-build.json`: "pytest: could not complete ... under Python 3.13", with `fastapi==0.95.2` and `pydantic==1.10.12` pinned.
  - `runs/20-provider-directory-semantic-search/20261124-200008/events.jsonl`: llama-index==0.10.0 and ==0.14.26 were both tried, and the final app/requirements.txt and code have no LlamaIndex.
  - `runs/20-identity-resolution-multi-agent/20261124-210002/doc-gaps.md`: reports `>=` pins, and a README with no clean-up and no offline-vs-live run matrix.
- Static re-scan of the latest app per slug (101 slugs): 38 requirements.txt have `>=` or unpinned entries, 2 Node apps have no lockfile, and 58 READMEs have no clean-up mention. All three match. A different file-name rule found 40 apps with no tests, against the draft's 35. The body now gives a range.
- CLI: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster lists `az documentdb mongocluster list-connection-strings`, example `--cluster-name MyCluster -g MyResourceGroup`. The `.env.example` hint now includes the required arguments.
- mongomock and mongodb-memory-server do not run Azure DocumentDB `cosmosSearch` vector or `$search` text-index queries. The body now says to stub those calls at the data-access layer.
- No claim contradicts the service facts: resource type `Microsoft.DocumentDB/mongoClusters`, CLI group `az documentdb mongocluster`, and vectors stored as number[].

### 3. Maintainer skeptic — confirmed

The fix belongs in the pipeline repo (abinav2307/azure-documentdb-agent-readiness), and the draft names exact files and insertion points, all of which exist: `prompts/builder.md` ("How to work" / "Limits"), `best-practices/checklist.md`, `requirements/retail-semantic-search.md` line 29 plus `loop/draft_requirements.py`, and `prompts/auditor.md` "Step 2". `factory/tools/` exists for the optional lint. It also has a DocumentDB angle: the CLI connection-string hint, and the fact that a Python-worded requirement wrongly failed a Node sample. It corrects 25 findings that were misrouted to Learn. I would accept it with the edits applied.

## Finding ids

F0271, F0276, F0334, F0336, F0337, F0443, F0444, F0445, F0515, F0542, F0903, F0933, F0986, F2171, F2229, F3196, F3247, F3313, F3341, F3381, F3383, F3406, F3448, F3482, F3516
