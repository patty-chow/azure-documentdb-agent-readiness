---
id: H12
title: "Build prompt and audit: require pinned dependencies with a lockfile, a valid .env.example and offline tests"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: needs_sme
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 18
member_drafts:
  - 082-pipeline-build-prompt-and-audit-checklist-requirements-for-s.md
open_questions: 3
---

# Build prompt and audit: require pinned dependencies with a lockfile, a valid .env.example and offline tests

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR.

## What happens today

The pipeline generates Azure DocumentDB samples with a builder agent and then audits them. The builder prompt (`prompts/builder.md`) asks for only two hygiene deliverables: "ship a `.env.example` with placeholder values" and a README covering "how to clean up". The team checklist (`best-practices/checklist.md`) already states the intent in general terms: `.env.example` lists every required setting, clean-up steps are provided, "Dependencies are pinned", and tests pass without a live cloud resource. But those rules are not carried into the build prompt, are not language-aware, and the auditor does not check them mechanically.

Worse, the shared gallery-hygiene block in `requirements/retail-semantic-search.md` (line 29), which `loop/draft_requirements.py` copies into all 101 generated requirements files, says "Dependencies are pinned in `requirements.txt`", so it names a Python file even for Node samples.

When a sample misses one of these, the auditor files it as a Microsoft Learn documentation gap (`learn_doc` / `discoverability`), which sends sample-scaffolding work to the product-docs team.

A static scan of the latest run of each of the 101 sample slugs found:

| Defect | Samples |
|---|---|
| `.env.example` omits a variable the code reads (e.g. `PORT`, `MAX_POOL_SIZE`, `DATABASE_NAME`) | 43 |
| `.env.example` has an unbalanced quote | 3 |
| Python `requirements.txt` with `>=` or unpinned entries | 38 |
| Node sample with no `package-lock.json` / `npm-shrinkwrap.json` | 2 |
| README with no Clean-up section | 58 |
| No tests at all | 35 to 40 (depends on which file-name patterns count) |

## Why it matters

In one experiment run of 100 samples, the auditor raised 25 findings across 18 distinct samples on this theme, and all of them are pipeline defects rather than Learn gaps. Counts come from that single run and may change after the related harness fixes (for example the Python 3.13 build-image issue) land. What the agent got wrong:

- **A correct sample failed.** `06-omnichannel-interaction-history` (Node) committed `package-lock.json`, yet the auditor marked "Dependencies are pinned in `requirements.txt`" as `partly_met` because the rule names a Python file.
- **Broken copy-paste.** `13-basel-iii-capital-ratio-calculator` ships a `.env.example` whose connection-string placeholder has no closing quote.
- **Tests never ran.** `19-option-chain-data-store` pinned pydantic 1.x and an old FastAPI. The README says "Python 3.10+", the runner had 3.13, and pytest could not run.
- **A requested feature was dropped.** `20-provider-directory-semantic-search` rewrote `requirements.txt` four times, then removed LlamaIndex, which the prompt had asked for.
- **No offline target.** `02-real-time-event-stream-ingestion`, `02-transaction-categorization-agent` and `20-store-locator-with-geospatial-search` ship no tests that run without the cluster; `20-identity-resolution-multi-agent` has unit tests, but its README never says which tests need `DOCUMENTDB_URI` or how to remove seeded data.

## Proposed change

### 1. `prompts/builder.md`: add after "How to work", before "Limits"

```markdown
## Deliverables every sample ships

Reviewers check these mechanically; a sample that misses one is sent back.

- **`.env.example`**, syntactically valid (every value quoted or unquoted consistently, no
  unbalanced quotes). It lists **every** environment
  variable any file in the sample reads (`process.env.X`, `os.environ[...]`, `os.getenv`),
  required ones first, each with a one-line comment and a placeholder value only
  (`<your-cluster-name>`, never a real host, user or key). Include the lines
  `# Get the connection string with: az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <resource-group>`
  and `# Copy to .env; never commit .env`.
- **Exact pins and a committed lockfile for the sample's language.**
  Python: `requirements.txt` with `==` for every package (or `pyproject.toml` plus a committed
  `poetry.lock` / `uv.lock` / `constraints.txt`). Node: exact versions in `package.json` and a
  committed `package-lock.json` or `npm-shrinkwrap.json`. Optional integrations (LlamaIndex,
  LangChain, Beanie, ...) go in their own pinned block (`requirements-extras.txt` or an npm
  optional group) that you install once and record as `verification_done`. Do not drop a
  framework the prompt asked for because the resolver failed; pin a working set instead.
- **Tested runtime.** The README states "Tested with Python 3.11" (or the Node major), and
  `engines` / `requires-python` says the same. Use the runtime the run environment provides
  and pin packages that support it.
- **Tests that run offline.** A `tests/` folder with fixtures (mongomock,
  mongodb-memory-server or driver mocks; a stubbed embedding client). Stub `cosmosSearch`
  vector queries and `$search` text queries at the data-access layer rather than expecting an
  emulator to run them. Provide a `test:unit` / `pytest -m "not live"` target that passes with
  no `.env`. Live tests are marked and skipped when `DOCUMENTDB_URI` is unset.
- **Seed script** that batches writes (`insert_many` / `bulk_write`, bounded batch size), is
  idempotent (upsert on a deterministic key), and takes `--force` to drop and reseed. A
  `sample-data.md` documents the seed document shape and any fixed taxonomy the sample uses.
- **README sections**, in this order: What this sample shows, Prerequisites, Setup (including
  `.env.example` to `.env`), Run, **Testing** (which tests are offline, which need the cluster
  and an API key, and the command for each), **Clean-up** (commands to drop the sample
  database or collections and to delete any Azure resources the IaC created).
```

### 2. `best-practices/checklist.md`

Under "Authentication and secrets", replace the existing `.env.example` bullet with:

```markdown
- A syntactically valid `.env.example` names every environment variable the code reads, with a one-line comment and a placeholder value each.
```

Replace the five-bullet "Sample hygiene" section with:

```markdown
## Sample hygiene

- The README has What-it-shows, Prerequisites, Setup, Run, Testing and Clean-up sections, and states the Python or Node version the sample was tested with.
- The sample runs with the commands in the README on that version.
- Dependencies are pinned for the sample's language: Python has `==` pins or a committed lockfile/constraints file; Node has a committed `package-lock.json` or `npm-shrinkwrap.json`. Optional extras are pinned and install-tested separately.
- Unit tests run and pass with no `.env` and no live cluster; tests that need the cluster are marked and skipped when `DOCUMENTDB_URI` is unset.
- The seed script is batched, idempotent, and documents its document shape.
- The sample names the service correctly and does not use a former or neighbouring product name.
```

### 3. `requirements/retail-semantic-search.md`: replace line 29

```markdown
- Dependencies are pinned for the sample's language (Python: exact versions in `requirements.txt` or a committed lockfile/constraints file; Node: a committed `package-lock.json` or `npm-shrinkwrap.json`).
- `.env.example` names every environment variable the code reads, with a placeholder and a comment each.
- The README has Testing and Clean-up sections and states the tested Python or Node version.
```

Then re-run `loop/draft_requirements.py` (it reads this block via `EXAMPLE = REQUIREMENTS / "retail-semantic-search.md"`) so all 101 generated files pick it up.

### 4. `prompts/auditor.md`: add after "Step 2: check the app against each practice"

```markdown
**Hygiene checks are judged against the sample's own language and files, not against a
Python template.** For dependency pinning, look for `==` pins or a committed lockfile when the
sample is Python, and for a committed `package-lock.json` or `npm-shrinkwrap.json` when it is
Node; a Node sample is not marked down for lacking `requirements.txt`. For `.env.example`, list
the variables the code reads (`process.env.X`, `os.environ[...]`, `os.getenv`), name each one
missing from the file, and flag any line with an unbalanced quote. For the README, confirm the
Testing and Clean-up headings exist and a tested runtime version is stated. A failure of any of
these is a `builder_error` with a prompt or checklist fix; it is never a `learn_doc` or
`discoverability` gap.
```

### 5. Optional follow-up

A small `factory/tools/hygiene_lint.py` run before the auditor (env-var diff, quote balance, per-language pin check, README headings, lockfile presence) would make these checks deterministic. It can come in a separate PR.

After this lands, the 25 findings listed below should be re-targeted from Learn to the pipeline and closed.

## Evidence

- `runs/06-omnichannel-interaction-history/20261124-204007/05-audit.json`
- `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/app/.env.example`
- `runs/19-option-chain-data-store/20261124-192712/03-build.json`
- `runs/20-provider-directory-semantic-search/20261124-200008/events.jsonl`
- `runs/20-identity-resolution-multi-agent/20261124-210002/doc-gaps.md`

Finding ids: F0271, F0276, F0334, F0336, F0337, F0443, F0444, F0445, F0515, F0542, F0903, F0933, F0986, F2171, F2229, F3196, F3247, F3313, F3341, F3381, F3383, F3406, F3448, F3482, F3516.

## Open questions

1. [needs SME confirmation] Should offline tests stub `cosmosSearch` and `$search` at the data-access layer (the text above assumes mongomock and mongodb-memory-server cannot run them), or should the prompt instead point builders at the local DocumentDB gateway container for those tests?
2. [needs SME confirmation] Is `az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <resource-group>` the command the team wants every sample's `.env.example` to show, or should it point to a Learn page instead?
3. The sample counts (18 samples, 25 findings, and the scan table) come from one run. Python 3.13 install failures in the build image inflate some of them. Should the counts be re-measured after the harness fixes before they are quoted outside the team?

## Source drafts

- 082-pipeline-build-prompt-and-audit-checklist-requirements-for-s.md
