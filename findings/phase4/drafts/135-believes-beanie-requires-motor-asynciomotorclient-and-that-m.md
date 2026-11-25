---
title: "connection skill: say Beanie 2.x runs on AsyncMongoClient so agents stop pairing Beanie with Motor"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 3
findings: 3
bucket: confusion-Q07
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# connection skill: say Beanie 2.x runs on AsyncMongoClient so agents stop pairing Beanie with Motor

## What happens today
`skills/connection/SKILL.md` (the "Python async note" blockquote, lines 45-49) correctly says to use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+) and not Motor. It says nothing about ODMs. Many sample prompts ask for **Beanie**, and the model's prior, taken from older Beanie docs, is that "Beanie requires an `AsyncIOMotorClient`". With the skill silent on that point, the agent sees two pieces of guidance that seem to conflict, hedges, and falls back to Motor.

In an agent-readiness run of 100 Azure DocumentDB sample prompts (gpt-5-mini, Agent Kit with the DocumentDB, Azure and Learn MCP servers), 3 Beanie samples were marked `partly_wrong` on the driver question (Q07). Grounded answers cited this skill and still hedged, for example "use Motor with Beanie, or adapt to AsyncPyMongo if Beanie supports it".

What each generated app actually did:
- **07-voice-of-customer-sentiment-hub**: `app/src/db.py` creates an `AsyncIOMotorClient` singleton and `app/scripts/run_aggregations.py` calls `Feedback.get_motor_collection()`. `requirements.txt` pins only `pymongo==4.20.1`; neither Motor nor Beanie is pinned, so the app as shipped cannot even import its own database layer.
- **17-ai-survey-response-analyzer**: pins `beanie==1.24.0`, `motor==3.1.1`, `pymongo==4.6.0`. The audit's discovered practice says to initialise Beanie "with an AsyncIOMotorClient".
- **09-clinical-notes-de-identification**: during readiness the agent found the Learn quickstart (Beanie 2 with `AsyncMongoClient`). It still shipped `beanie==1.26.0`, `motor==3.1.1`, `pymongo==4.6.0`, and the audit marks "Driver version choice" as **violated**.

## Why it matters
MongoDB deprecated Motor in May 2024; it received only critical fixes through May 2026 and is now end of life, so all three samples shipped on an end-of-life driver. The skill already takes the right position; it just doesn't carry it through to the ODM most Python samples use. The Learn page https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie already shows `beanie==2.2.0` with `AsyncMongoClient`, so no docs change is needed. The skill only has to state the point and link the page.

## Proposed change
In `skills/connection/SKILL.md`, extend the "Python async note" blockquote:

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

In `skills/driver/SKILL.md`, which currently has only a `## Rules` list (one entry, `driver-singleton-client`) and no language-specific section, add one line below that list: "Python async / Beanie: use `AsyncMongoClient` (PyMongo 4.9+) and Beanie 2, never Motor. See the Python async note in `documentdb-connection`."

Optional follow-up for the Learn team: run 17's audit attributes the "initialise Beanie with an AsyncIOMotorClient" practice to `tutorial-python-beanie#prerequisites`. Check whether that tutorial page still shows Motor.

## Evidence
- runs/07-voice-of-customer-sentiment-hub/20261124-204049 (02-readiness.json confusions Q07; app/src/db.py; app/scripts/run_aggregations.py; app/requirements.txt)
- runs/17-ai-survey-response-analyzer/20261124-205518 (02-readiness.json Q07; app/requirements.txt; 05-audit.json)
- runs/09-clinical-notes-de-identification/20261124-194349 (02-readiness.json Q07; app/requirements.txt; 05-audit.json "Driver version choice" status violated)

## Verification

### 1. Already covered? partially_covered
The connection skill covers the driver half but not the ODM half. `skills/connection/SKILL.md` lines 45-49: "Use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+), **not** Motor." A grep for `beanie` across `skills/` and `knowledge-base/` in the agent-kit clone returns nothing; `motor` appears only in that note. `skills/driver/SKILL.md` has no Python guidance at all. The Learn quickstart (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-beanie, fetched 2026-11-25) already shows `beanie==2.2.0` and `AsyncMongoClient`, so Learn needs no change; the gap is in the kit where agents look first.

### 2. Premise true? confirmed
- Motor deprecation (May 2024) and end of life (May 2026) match the kit's own note and MongoDB's announcement.
- Beanie 2.0 migrated from Motor to PyMongo's async API (`AsyncMongoClient`) and renamed `get_motor_collection()` to `get_pymongo_collection()` (Beanie 2.0 release notes and migration guide).
- The Learn Beanie quickstart pins `beanie==2.2.0` and uses `AsyncMongoClient` (page fetched).
- Run evidence checked directly: run 17 and run 09 `requirements.txt` pin Beanie 1.x with `motor==3.1.1`; run 07 `db.py` uses `AsyncIOMotorClient` and `run_aggregations.py` uses `get_motor_collection()`; run 09 audit "Driver version choice" status is `violated`.
Edits applied: clarified that run 07 pins only `pymongo` (Motor import would fail); added `import os` to the snippet; noted Beanie 2.0 dropped Motor; corrected the driver-skill placement, since that skill has no "Python guidance" section.

### 3. Maintainer skeptic: confirmed
Names exact files and a specific, small text change in the skill that already owns the Motor guidance, tied to an Azure DocumentDB Learn quickstart. Not generic hygiene; it extends an existing kit position to the ODM that most Python samples use. I would accept it with the small placement edit applied.

## Finding ids
- F1162
- F1371
- F2807
