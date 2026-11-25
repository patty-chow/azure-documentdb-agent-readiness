---
title: "driver skill: add a \"reproducible installs\" rule (resolve versions from the registry, lock, npm ci / pinned requirements) plus a tested-stack matrix"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 11
findings: 11
bucket: kit-doc-gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# driver skill: add a "reproducible installs" rule (resolve versions from the registry, lock, `npm ci` / pinned requirements) plus a tested-stack matrix

## What happens today

`skills/driver/SKILL.md` is the skill an agent loads whenever it writes code that instantiates a MongoDB client. It links one rule (`driver-singleton-client.md`) and says nothing about how the generated project should declare or install its dependencies. The `documentdb-connection` skill tells agents to use PyMongo `AsyncMongoClient` instead of Motor, but no skill says which versions of the drivers/ODMs the kit has verified, or how a sample should pin them.

The kit's own `compat/` workload already does the right thing (`"mongodb": "6.20.0"` in `compat/package.json`, `npm ci` in `compat/QUICKSTART.md`), but that convention is never stated as guidance, so agents do not follow it.

## Why it matters

In a 100-sample run of the DocumentDB Agent Kit with gpt-5-mini, 11 samples were flagged by the audit for this gap (7 of them `high`). The concrete failures:

- **Versions invented from memory.** `npm install` failed twice in the ATM monitor sample with `ETARGET: No matching version found for supertest@^6.4.3` (then `^6.4.4`), a version that does not exist; the build stopped and seed/start/tests never ran. In the order-history sample, `pip install` failed on `pymongo==4.5.1` and `langchain==0.0.418` (also nonexistent); the agent's recorded fix (decisions D009/D010) was to **relax the pins to `>=` ranges**, trading away reproducibility to get past the error.
- **Ranges where pins were expected.** 7 Python samples shipped `requirements.txt` with `>=` ranges or bare names (`fastapi`, `langchain`, `openai`, `pymongo>=4.5`), which the audit flagged as reproducibility and driver wire-compatibility risks. Where the agent did pin, it pinned to its training-era versions (`openai==0.27.0`, `langchain>=0.0.300`, `motor==3.1.1`).
- **Node lockfile without a lockfile policy.** 2 Node samples committed `package-lock.json` but kept caret ranges in `package.json` and told users to run `npm install`, not `npm ci`.
- **Stack choice contradicting the kit.** The survey-analyzer sample pinned `beanie==1.24.0` + `motor==3.1.1` even though `skills/connection/SKILL.md` says not to use Motor. There is no table saying which Beanie line goes with PyMongo's async client and which with Motor, so the agent picked the combination it remembered.

A plain "pin exact versions" rule would not have fixed the first bullet: the agent would have pinned a hallucinated version. The rule has to say **resolve first, then lock**.

## Proposed change

### 1. New rule file: `skills/driver/driver-reproducible-installs.md`

Follows the existing rule template (Why it matters / Incorrect / Correct / References). Proposed content:

```markdown
# driver-reproducible-installs — Resolve versions from the registry, then lock them

## Why it matters
A sample that installs differently tomorrow than it did when it was verified is not a sample. Driver
versions also gate wire-protocol features (for example PyMongo >= 4.9 for `AsyncMongoClient`), so
an unpinned driver can silently change what works against Azure DocumentDB. Agents must never write
a version they remember; they must look it up.

## Rules
1. **Resolve before you write.** Before adding a dependency, query the registry and use a version it
   returns: `npm view <pkg> version` / `npm view <pkg> versions --json`, or
   `pip index versions <pkg>` (pip >= 21.2). Never copy a version from memory or from an old
   tutorial; if the lookup fails, say so instead of guessing.
2. **Node samples** commit `package-lock.json`, use exact versions (no `^`/`~`) for the DocumentDB
   client and ODM (`mongodb`, `mongoose`), and tell users to run `npm ci`, not `npm install`.
   CI runs `npm ci` too, so an out-of-date lockfile fails fast.
3. **Python samples** ship an exact-pinned `requirements.txt` (or `requirements.in` +
   `pip-compile`d `requirements.txt`) that matches the interpreter used for verification, and the
   README carries one line: `Tested on Python 3.12 / pip 24.x`.
4. **Ranges are for libraries, not samples.** A `>=` floor is acceptable only in a package others
   depend on. A runnable sample pins everything it imports.
5. **Updating pins is a deliberate step.** Re-run the resolve step, regenerate the lockfile, re-run
   the sample's seed/verify, then commit the new pins with the CHANGELOG line.

## Incorrect
```json
"devDependencies": { "supertest": "^6.4.3" }     // version never existed; npm install -> ETARGET
```
```text
pymongo>=4.5          # floats; a future 5.x could change behaviour under the sample
langchain             # resolves to whatever is newest today
```
README: `npm install`

## Correct
```bash
npm view mongodb version          # -> 6.x.y (use the value printed)
npm install --save-exact mongodb@6.x.y
npm ci                            # what the README and CI run
```
```bash
python -m pip install pip-tools
pip index versions pymongo        # confirm the version exists before pinning
pip-compile requirements.in       # produces exact-pinned requirements.txt
python -m pip install -r requirements.txt
```
README: `Tested on Python 3.12 / pip 24.3 — regenerate pins with pip-compile requirements.in`

## Tested stacks (fill from CI; keep this table short)
| Language | Client / ODM | Verified version | Notes |
|---|---|---|---|
| Node.js | `mongodb` | 6.20.0 (as pinned in `compat/package.json`) | |
| Node.js | `mongoose` | <fill> | wraps `mongodb` above |
| Python  | `pymongo` (sync `MongoClient`) | <fill> | |
| Python  | `pymongo` (`AsyncMongoClient`) | >= 4.9, verified <fill> | preferred async client |
| Python  | `beanie` 2.x | <fill> | uses PyMongo's async client; Beanie 2.0.0 declares `pymongo>=4.11,<5` and no Motor dependency |
| Python  | `beanie` 1.x + `motor` | not recommended | Motor is deprecated (see `documentdb-connection`) |

## References
- npm: `npm ci` docs; `npm view`
- pip-tools `pip-compile`; `pip index versions`
- `skills/connection/SKILL.md` (Python async note)
```

Maintainers should replace `<fill>` with the versions actually exercised by `evals/` and `testing/` so the table is a statement of fact, not a guess. For the Beanie rows, the floor is already known from PyPI metadata: Beanie 2.0.0 requires `pymongo>=4.11.0,<5.0.0` and drops Motor, so a Beanie 2.x sample needs PyMongo 4.11 or later (not just the 4.9 floor for `AsyncMongoClient`).

### 2. Link it from `skills/driver/SKILL.md`

Add under `## Rules`:

```markdown
- [driver-reproducible-installs](driver-reproducible-installs.md) — Resolve dependency versions from the registry (never from memory), commit lockfiles, `npm ci` / exact-pinned `requirements.txt`, tested-stack matrix.
```

and extend the frontmatter `description` with "dependency pinning and lockfiles for samples".

### 3. One cross-reference in `skills/connection/SKILL.md`

Under `## When Creating Code` (line ~260) add: "Pin the driver version you verified against; see `documentdb-driver` → `driver-reproducible-installs`."

### 4. CHANGELOG entry

"Added `driver-reproducible-installs` rule: registry-resolved versions, lockfile + `npm ci`, pinned `requirements.txt`, tested-stack matrix."

(Side note: `CONTRIBUTING.md` still points at `skills/documentdb-best-practices/rules/`, which no longer exists; the rule above follows the per-skill layout the repo actually uses.)

## Evidence (run folders from the 100-sample experiment)

- `runs/16-atm-network-status-monitor/20261124-202405/events.jsonl` — two `npm install` failures, `ETARGET ... supertest@^6.4.3` / `^6.4.4`; build halted.
- `runs/06-order-history-timeline-agent/20261124-183612/decisions.jsonl` — D009/D010: `pymongo==4.5.1` and `langchain==0.0.418` not found, pins relaxed to `>=` ranges.
- `runs/17-ai-survey-response-analyzer/20261124-205518/app/requirements.txt` — `beanie==1.24.0`, `motor==3.1.1` despite the connection skill's Motor guidance.
- `runs/04-natural-language-product-search/20261124-183232/app/requirements.txt` — nine dependencies, zero pins.
- `runs/02-transaction-categorization-agent/20261124-190028/app/package.json` — caret ranges beside a committed `package-lock.json`; README says `npm install`.

Related findings (same theme): F0338, F0478, F0648, F0960, F1608, F1772, F1910, F2005, F2668, F2830, F2896 — 11 distinct samples out of 100.

## Verification

### 1. Already covered? -- confirmed (not covered)
- `skills/driver/SKILL.md` lists a single rule (`driver-singleton-client`); the skill description covers "singleton `MongoClient`, connection reuse, connection-pool fundamentals" only. `skills/driver/` contains only `SKILL.md` and `driver-singleton-client.md`.
- `grep -rni "lockfile|npm ci|pinned|pip-compile|pip freeze|requirements.txt|save-exact"` over `skills/` and `knowledge-base/` finds nothing about application dependencies. The only "pin" guidance is for Docker images in `skills/local-deployment/local-docker-compose-setup.md` ("Pin the image ...") and `local-prod-parity.md` ("Version-pin the local image"), which do not cover npm/pip manifests.
- The convention exists in practice but not as guidance: `compat/package.json` line 14 `"mongodb": "6.20.0"`; `compat/QUICKSTART.md` line 38 `npm ci`.
- No tested-versions matrix exists; `skills/connection/SKILL.md` lines 45-49 say to use PyMongo `AsyncMongoClient` (4.9+) and not Motor, but give no Beanie/ODM compatibility guidance.

### 2. Premise true? -- confirmed (one cell filled in)
- supertest: `npm view supertest versions` lists 6.x only up to 6.3.4, so `^6.4.3` / `^6.4.4` cannot resolve; matches the `ETARGET ... No matching version found for supertest@^6.4.3` / `^6.4.4` lines in `runs/16-atm-network-status-monitor/20261124-202405/events.jsonl`.
- PyPI returns 404 for `pymongo/4.5.1` and `langchain/0.0.418`; `runs/06-order-history-timeline-agent/20261124-183612/decisions.jsonl` D009/D010 record relaxing them to `pymongo>=4.5,<5` and `langchain>=0.0.331,<1`.
- `runs/17-ai-survey-response-analyzer/.../app/requirements.txt` has `beanie==1.24.0`, `motor==3.1.1`; `runs/04-natural-language-product-search/.../app/requirements.txt` has no pins (`pymongo>=4.5`, bare `fastapi`, `langchain`, `openai`, ...); `runs/02-transaction-categorization-agent/.../app/package.json` uses caret ranges (`"mongodb": "^5.9.0"`) beside a committed `package-lock.json`, and its README step 2 is `npm install`.
- Motor deprecation and the PyMongo 4.9+ `AsyncMongoClient` floor match `skills/connection/SKILL.md` lines 45-49.
- Correction applied: the draft left the Beanie 2.x floor as "verify the exact minimum". PyPI metadata for beanie 2.0.0 (https://pypi.org/pypi/beanie/2.0.0/json) declares `pymongo<5.0.0,>=4.11.0` and no Motor dependency, so the matrix row and the maintainer note now say that.
- `npm ci`, `npm install --save-exact`, `pip index versions` (pip 21.2+) and `pip-compile` (pip-tools) are standard tooling, used correctly. Nothing in the draft contradicts the Azure DocumentDB facts.

### 3. Maintainer skeptic -- confirmed
- Names concrete files: new `skills/driver/driver-reproducible-installs.md` (follows the existing rule template), a link in `skills/driver/SKILL.md` under `## Rules`, a cross-reference under `## When Creating Code` in `skills/connection/SKILL.md` (line 260), and a `CHANGELOG.md` entry. All of these paths exist.
- It has an Azure DocumentDB angle: the kit's own connection skill steers toward PyMongo `AsyncMongoClient`, and samples broke or drifted against it. The rule also codifies what the kit already does in `compat/`. The "resolve from the registry first" step deals with a failure mode specific to agents (made-up versions), so this is more than generic hygiene.
- `<fill>` cells are explicitly left for maintainers to fill from `evals/` / `testing/`, which is acceptable for a PR. The side note is accurate: `CONTRIBUTING.md` lines 8-15 still point at `skills/documentdb-best-practices/rules/`, which does not exist.

## Finding ids

- F0338
- F0478
- F0648
- F0960
- F1608
- F1772
- F1910
- F2005
- F2668
- F2896
- F2830
