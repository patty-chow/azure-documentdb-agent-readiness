---
id: K37
title: "connection skill: Beanie 2.x runs on AsyncMongoClient, not Motor"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P2
sample_count: 3
member_drafts:
  - 135-believes-beanie-requires-motor-asynciomotorclient-and-that-m.md
open_questions: 2
---

# connection skill: Beanie 2.x runs on AsyncMongoClient, not Motor

## What happens today

The "Python async note" blockquote in `skills/connection/SKILL.md` (lines 45-49) is correct: it says to use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+) and not Motor. It says nothing about ODMs, though. Neither `skills/` nor `knowledge-base/` mentions Beanie anywhere, and `skills/driver/SKILL.md` has no Python guidance at all.

Many Python app prompts ask for **Beanie**. Older Beanie docs taught coding agents that "Beanie requires an `AsyncIOMotorClient`". Because the skill says nothing about Beanie, the agent reads the two pieces of guidance as a conflict. It hedges ("use Motor with Beanie, or adapt to AsyncPyMongo if Beanie supports it") and ends up using Motor. This happened even in answers that cited the skill.

What the generated apps actually did:
- **voice-of-customer-sentiment-hub**: `app/src/db.py` creates an `AsyncIOMotorClient` singleton, and `app/scripts/run_aggregations.py` calls `Feedback.get_motor_collection()`. `requirements.txt` pins only `pymongo`. Neither Motor nor Beanie is pinned, so the app as shipped cannot import its own database layer.
- **ai-survey-response-analyzer**: pins `beanie==1.24.0`, `motor==3.1.1` and `pymongo==4.6.0`. Its audit records the practice "initialise Beanie with an AsyncIOMotorClient".
- **clinical-notes-de-identification**: the agent found the Learn quickstart, which uses Beanie 2 with `AsyncMongoClient`. It still shipped `beanie==1.26.0` and `motor==3.1.1`, and its audit marks "Driver version choice" as violated.

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample-app prompts, built by a coding agent that had this Agent Kit plus the DocumentDB, Azure and Learn MCP servers. In 3 of the 100 samples, the driver question came out partly wrong, and all 3 wrote their Beanie database layer on Motor (two pin Beanie 1.x with Motor; the third uses Motor in code but pins neither). These counts come from one experiment run.

MongoDB has deprecated Motor in favour of PyMongo's async API, so all three apps shipped on a deprecated driver. The kit's note dates this as deprecation in May 2024 with critical fixes only through May 2026 and end of life after that [needs SME confirmation: MongoDB's own Motor notice may date the deprecation to May 2025, with end of life later than May 2026; confirm the dates before this PR repeats them]. Beanie 2.0 dropped Motor and moved to PyMongo's async API. The Learn quickstart (https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie) already shows `beanie==2.2.0` with `AsyncMongoClient`, so the docs need no change. The kit already takes the right position on drivers. This PR carries that position through to the ODM that most Python samples use, and links the quickstart.

## Proposed change

**1. `skills/connection/SKILL.md`**: add the following lines to the end of the existing "Python async note" blockquote:

```markdown
> **ODMs:** Beanie 2.x accepts PyMongo's `AsyncMongoClient` directly (Beanie 2.0
> dropped Motor). Do not pair Beanie with Motor and do not pin Beanie 1.x for
> new code. Pin `beanie>=2` and `pymongo>=4.9`, and initialise like this:
>
> ```python
> import os
> from pymongo import AsyncMongoClient
> from beanie import init_beanie
> client = AsyncMongoClient(os.environ["DOCUMENTDB_URI"])
> await init_beanie(database=client[DB_NAME], document_models=[...])
> ```
> Use `Document.get_pymongo_collection()` (Beanie 2's replacement for
> `get_motor_collection()`) for raw aggregations.
> Reference: https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie
```

[needs SME confirmation: the `pymongo>=4.9` floor is a driver version floor; PyMongo's async API first shipped as beta in 4.9 and reached GA in a later 4.x release. Confirm whether the floor should be 4.9 (as the kit's existing note says) or the GA release.]

**2. `skills/driver/SKILL.md`**: this file has only a `## Rules` list, with one entry (`driver-singleton-client`), and no language-specific section. Add one line below that list:

```markdown
Python async / Beanie: use `AsyncMongoClient` (PyMongo 4.9+) and Beanie 2, never Motor. See the Python async note in `documentdb-connection`.
```

Possible follow-up for the Learn team, outside this PR: one run's audit traced the "initialise Beanie with an AsyncIOMotorClient" practice to `tutorial-python-beanie#prerequisites`. Someone should check whether that tutorial page still shows Motor.

## Evidence

- `runs/07-voice-of-customer-sentiment-hub/20261124-204049`: `02-readiness.json` (Q07 confusion), `app/src/db.py`, `app/scripts/run_aggregations.py`, `app/requirements.txt`
- `runs/17-ai-survey-response-analyzer/20261124-205518`: `02-readiness.json` (Q07), `app/requirements.txt`, `05-audit.json`
- `runs/09-clinical-notes-de-identification/20261124-194349`: `02-readiness.json` (Q07), `app/requirements.txt`, `05-audit.json` ("Driver version choice": violated)

## Open questions

1. Motor dates. The kit's note (and this PR's rationale) says Motor was deprecated in May 2024, got critical fixes only through May 2026, and is now end of life. MongoDB's own notice may give May 2025 for the deprecation and a later end of life. An SME should confirm the dates; if the kit's note is wrong, fix those lines in the same PR.
2. PyMongo floor. Should the pinned floor be `pymongo>=4.9` (first release with the async API, as beta) or the release where `AsyncMongoClient` became GA? The reviewer's section 5 lists driver version floors as needing SME confirmation.

The change does not touch the retryWrites setting or any other point where the drafts disagree. The draft's verifier checked the Beanie 2.0 move to `AsyncMongoClient` and the `get_pymongo_collection()` rename against the Beanie 2.0 release notes, and the Learn quickstart page. Sample counts come from one experiment run; the reviewer advises re-running before quoting them externally.

## Source drafts

- 135-believes-beanie-requires-motor-asynciomotorclient-and-that-m.md
