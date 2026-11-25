---
id: K29
title: "driver skill: add a reproducible-installs rule (resolve versions from the registry, lock, npm ci / pinned pip) plus a tested-stack matrix"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 11
member_drafts:
  - 088-reproducible-installs-dependency-pinning-lockfile-policy-and.md
open_questions: 3
---

# driver skill: add a reproducible-installs rule (resolve versions from the registry, lock, `npm ci` / pinned pip) plus a tested-stack matrix

## What happens today

`skills/driver/SKILL.md` is the skill an agent loads whenever it writes code that creates a MongoDB client. It links one rule (`driver-singleton-client.md`) and says nothing about how a generated project should declare or install its dependencies. `skills/connection/SKILL.md` (lines 45-49) says to use PyMongo `AsyncMongoClient` (4.9+) rather than Motor, but no skill says which driver/ODM versions the kit has verified or how a sample should pin them.

The kit already follows a good convention in its own `compat/` workload (`"mongodb": "6.20.0"` in `compat/package.json`, `npm ci` in `compat/QUICKSTART.md`), but it is never stated as guidance. A search of `skills/` and `knowledge-base/` for lockfile, `npm ci`, `pip-compile`, `requirements.txt` or `--save-exact` finds nothing about application dependencies; the only "pin" guidance is for Docker images in the local-deployment skill.

## Why it matters

We ran the kit with an AI coding agent (gpt-5-mini) against 100 sample app specs on Azure DocumentDB. In 11 of the 100 samples (7 rated high severity), the agent's dependency handling broke or drifted the build. Counts are from one experiment run and should be re-checked on a re-run before they are quoted externally (see Open questions 3).

- **Versions invented from memory.** One Node sample failed `npm install` twice with `ETARGET` for `supertest@^6.4.3` and then `^6.4.4`; the 6.x line stops at 6.3.4, so the build halted and nothing after it ran. A Python sample failed `pip install` on `pymongo==4.5.1` and `langchain==0.0.418`, which do not exist on PyPI; the agent "fixed" it by relaxing both to `>=` ranges, trading away reproducibility.
- **Ranges where pins were expected.** 7 Python samples shipped `requirements.txt` with `>=` ranges or bare names. Where the agent did pin, it used training-era versions (`openai==0.27.0`, `motor==3.1.1`).
- **Lockfile without a lockfile policy.** 2 Node samples committed `package-lock.json` but kept caret ranges and told users to run `npm install`, not `npm ci`.
- **Stack contradicting the kit.** One sample pinned `beanie==1.24.0` + `motor==3.1.1` although the connection skill says not to use Motor; nothing says which Beanie line pairs with PyMongo's async client.

A plain "pin exact versions" rule would not fix the first bullet: the agent would pin a hallucinated version. The rule must say **resolve first, then lock**.

## Proposed change

### 1. New file `skills/driver/driver-reproducible-installs.md` (follows the existing rule template)

~~~markdown
# driver-reproducible-installs — Resolve versions from the registry, then lock them

## Why it matters
A sample that installs differently tomorrow than it did when it was verified is not a sample. Driver
versions also gate features (for example PyMongo >= 4.9 for `AsyncMongoClient`), so an unpinned
driver can silently change what works against Azure DocumentDB. Never write a version you remember;
look it up.

## Rules
1. **Resolve before you write.** Before adding a dependency, query the registry and use a version it
   returns: `npm view <pkg> version` / `npm view <pkg> versions --json`, or
   `pip index versions <pkg>` (pip >= 21.2). Never copy a version from memory or an old tutorial;
   if the lookup fails, say so instead of guessing.
2. **Node samples** commit `package-lock.json`, use exact versions (no `^`/`~`) for the client and
   ODM (`mongodb`, `mongoose`), and tell users to run `npm ci`, not `npm install`. CI runs `npm ci`
   too, so an out-of-date lockfile fails fast.
3. **Python samples** ship an exact-pinned `requirements.txt` (or `requirements.in` +
   `pip-compile`d `requirements.txt`) matching the interpreter used for verification, and the
   README carries one line: `Tested on Python 3.12 / pip 24.x`.
4. **Ranges are for libraries, not samples.** A `>=` floor is acceptable only in a package others
   depend on. A runnable sample pins everything it imports.
5. **Updating pins is a deliberate step.** Re-run the resolve step, regenerate the lockfile, re-run
   the sample's seed/verify, then commit the new pins with a CHANGELOG line.

## Incorrect
```json
"devDependencies": { "supertest": "^6.4.3" }     // version never existed; npm install -> ETARGET
```
```text
pymongo>=4.5          # floats; a future major could change behaviour under the sample
langchain             # resolves to whatever is newest today
```
README: `npm install`

## Correct
```bash
npm view mongodb version          # use the value printed
npm install --save-exact mongodb@<printed-version>
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
- npm: `npm ci`, `npm view`
- pip-tools `pip-compile`; `pip index versions`
- `skills/connection/SKILL.md` (Python async note)
~~~

Maintainers should replace each `<fill>` with versions actually exercised by `evals/` and `testing/`, so the table states fact. [needs SME confirmation] The driver version floors in this rule (PyMongo 4.9 for `AsyncMongoClient`, PyMongo 4.11 for Beanie 2.x) must be confirmed against what the kit has tested on Azure DocumentDB before merge (see Open questions 1). The Beanie 2.x floor comes from PyPI metadata (2.0.0 requires `pymongo>=4.11.0,<5.0.0`, no Motor), so a Beanie 2.x sample needs PyMongo 4.11+, not just the 4.9 `AsyncMongoClient` floor.

### 2. `skills/driver/SKILL.md`

Under `## Rules` add:

```markdown
- [driver-reproducible-installs](driver-reproducible-installs.md) — Resolve dependency versions from the registry (never from memory), commit lockfiles, `npm ci` / exact-pinned `requirements.txt`, tested-stack matrix.
```

and extend the frontmatter `description` with "dependency pinning and lockfiles for samples".

### 3. `skills/connection/SKILL.md`

Under `## When Creating Code` (around line 260) add: "Pin the driver version you verified against; see `documentdb-driver` → `driver-reproducible-installs`."

### 4. `CHANGELOG.md`

"Added `driver-reproducible-installs` rule: registry-resolved versions, lockfile + `npm ci`, pinned `requirements.txt`, tested-stack matrix."

Side note, not part of this PR: `CONTRIBUTING.md` (lines 8-15) still points at `skills/documentdb-best-practices/rules/`, which no longer exists; this rule follows the per-skill layout the repo actually uses.

## Evidence

Run folders from the experiment:

- `runs/16-atm-network-status-monitor/20261124-202405/events.jsonl` — two `npm install` `ETARGET` failures for `supertest`; build halted.
- `runs/06-order-history-timeline-agent/20261124-183612/decisions.jsonl` — D009/D010: nonexistent `pymongo`/`langchain` pins relaxed to `>=` ranges.
- `runs/17-ai-survey-response-analyzer/20261124-205518/app/requirements.txt` — `beanie==1.24.0`, `motor==3.1.1`.
- `runs/04-natural-language-product-search/20261124-183232/app/requirements.txt` — nine dependencies, zero pins.
- `runs/02-transaction-categorization-agent/20261124-190028/app/package.json` — caret ranges beside a committed `package-lock.json`; README says `npm install`.

## Open questions

1. [needs SME confirmation] Driver version floors: confirm the PyMongo `AsyncMongoClient` floor (4.9) and the versions of `mongodb`, `mongoose`, `pymongo` and `beanie` that the kit's CI has actually verified against Azure DocumentDB, so every `<fill>` cell is a tested fact rather than a guess.
2. [needs SME confirmation] Confirm the kit wants Beanie 2.x (PyMongo async client) as the recommended Python ODM path and Beanie 1.x + Motor marked "not recommended", consistent with the Motor guidance in `skills/connection/SKILL.md`.
3. [needs SME confirmation] The sample count (11 of 100) comes from one run with one model; some Python install failures in that run may be environment artifacts (for example interpreter-version issues) rather than pinning gaps. The count should be re-checked on a re-run before it is quoted externally; the rule is justified by the made-up-version failures regardless.

## Source drafts

- 088-reproducible-installs-dependency-pinning-lockfile-policy-and.md
