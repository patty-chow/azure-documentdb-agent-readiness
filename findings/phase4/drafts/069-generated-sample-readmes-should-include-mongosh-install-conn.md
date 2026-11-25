---
title: 'Builder prompt: ask for a "Verify by hand" README section (mongosh); readiness prompt: keep URLs out of recommendation prose'
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P2
sample_count: 4
findings: 4
bucket: other-inventory
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Builder prompt: require a "Verify by hand" README section; readiness prompt: no URLs in recommendation prose

## What happens today

- The harness environment has no `mongosh` on PATH (`02-inventory.json` reports `"mongosh": not found` in every run). The readiness stage therefore emits an `inventory_recommendations[mongosh]` entry in 117 runs; 114 of them (98 distinct samples) mark it `worth_adding: true`, and 12 add that the sample README should tell developers how to install mongosh and connect for quick manual checks.
- `prompts/builder.md` step 3 asks for a README with "what the sample shows, prerequisites, setup, how to run, and how to clean up". Nothing asks for a manual-verification path, so only 11 of 112 generated `app/README.md` files mention mongosh, and those that do (e.g. 16-loyalty-points-ledger) only say "see mongosh/portal" in the clean-up section.
- In `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` the model wrote `https://learn.microsoft.com/mongodb/mongodb-shell/install` into the recommendation text and told the builder to put it in the README. That path does not exist (404 after the locale redirect). `prompts/readiness_checker.md` line 39 already says "Never construct or recall a URL", but it sits at the end of the per-confusion field list (`grounding_links`, `confusion_sources`, `improvements`), so it reads as scoped to confusions; the "Inventory recommendations" paragraph (line 45) and the free-text `recommendation` field are not covered, and the `references` array for that entry pointed at the agent-kit local-deployment skill and a legacy Cosmos DB page instead.

## Why it matters

- Every one of the 100 samples hit the missing-tool recommendation, which is harness noise rather than a product gap, and it crowds the findings bucket.
- A sample README without a "connect and look" step leaves a developer who cloned it with no quick way to confirm the cluster, user and indexes are right before debugging app code. The 12 runs that asked for it were right; the builder prompt never relayed the ask.
- An invented Learn URL is exactly the failure the audit stage is designed to catch for practices, but readiness output is not checked the same way, so a fabricated link can flow straight into a generated README.

## Proposed change

### 1. `prompts/builder.md`, step 3

Replace

> Include a README with what the sample shows, prerequisites, setup, how to run, and how to clean up.

with

> Include a README with what the sample shows, prerequisites, setup, how to run, a short **Verify by hand** section, and how to clean up. The Verify by hand section shows one `mongosh "$DOCUMENTDB_CONNECTION_STRING"` command (SRV connection string read from an environment variable, never written out) followed by one or two one-line checks such as `db.runCommand({ ping: 1 })` and `db.<collection>.getIndexes()`. If the sample also runs against the local Docker DocumentDB gateway, say that `--tlsAllowInvalidCertificates` is for that local gateway only. Link only to pages you obtained from a tool result: the Learn page "Connect using MongoDB Shell - Azure DocumentDB" (`https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell`) and the official mongosh install page on mongodb.com (`https://www.mongodb.com/docs/mongodb-shell/install/`). Do not invent a Learn path for mongosh installation.

### 2. `prompts/readiness_checker.md`

- Move the sentence "Never construct or recall a URL. If you do not have one from a tool result or skill text, leave it empty." out of the per-confusion section (it follows the `grounding_links`/`confusion_sources`/`improvements` list) into a top-level rule that applies to every field of the output, prose included.
- In the "Inventory recommendations" paragraph (line 45) add: "Put any URL in that entry's `references`, copied from a tool result; do not write URLs in `recommendation` text."
- Optional, in the pipeline: after each stage, HEAD-check every `http(s)://` string in the stage JSON and record a `dead_url` warning for anything that resolves to 404, so a fabricated link is flagged before the builder reads it.

### 3. Harness environment (no repo change)

Install mongosh where the runs execute (`brew install mongosh` or `npm install -g mongosh`), so `02-inventory.json` reports it available and the readiness stage stops recommending it in every run. `factory/config.py` already lists `mongosh` among allowed commands.

### Out of scope

No change is proposed for Azure/documentdb-agent-kit, microsoft/documentdb-mcp or Microsoft Learn. The Learn page for connecting with mongosh exists and was cited correctly by three of the four runs; only the harness prompts and environment need to change.

## Evidence

- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` - inventory_recommendations[mongosh], asks for README usage notes (and `--tlsAllowInvalidCertificates` for the local gateway)
- `runs/17-esg-scoring-pipeline/20261124-192259/02-readiness.json` - inventory_recommendations[mongosh], "Document the install command in the README"
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` - fabricated `learn.microsoft.com/mongodb/mongodb-shell/install`
- `runs/18-sanctions-list-screening-agent/20261124-202645/02-readiness.json` - inventory_recommendations[mongosh], "README should advise using mongosh with the SRV connection string"
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/app/README.md` - generated README with no manual-verification section

## Verification

### 1. Already covered? - confirmed
The target is the harness repo (abinav2307/azure-documentdb-agent-readiness). Local copy checked:
- `prompts/builder.md` line 29: "Include a README with what the sample shows, prerequisites, setup, how to run, and how to clean up." No manual-verification or mongosh step.
- `prompts/readiness_checker.md` line 39: "Never construct or recall a URL. If you do not have one from a tool result or skill text, leave it empty." It closes the per-confusion field list; the Inventory recommendations paragraph (line 45) has no URL rule, and the inventory `references` rule (line 47) does not forbid URLs in `recommendation` prose.
- Only 11 of 112 `runs/*/*/app/README.md` files mention mongosh.
- `mongosh` is not on PATH on the harness machine (`which mongosh` -> not found), although `factory/config.py` line 16 lists it among allowed commands.
Not covered in the harness; the Learn page the README should link to does exist (see check 2).

### 2. Premise true? - confirmed (one small wording correction applied)
- Counts re-computed from `runs/*/*/02-readiness.json`: 117 mongosh `inventory_recommendations` entries, 114 with `worth_adding: true` across 98 distinct samples, 12 mentioning the README. Matches the draft.
- `https://learn.microsoft.com/mongodb/mongodb-shell/install` returns HTTP 404; it appears in `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` with "(document this link in the README)".
- `https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell` returns HTTP 200 (Connect using MongoDB Shell - Azure DocumentDB); `https://www.mongodb.com/docs/mongodb-shell/install/` returns HTTP 200.
- `inventory_recommendations` entries have fields name, recommendation, worth_adding, references (`factory/models.py` line 123), so "put URLs in `references`" is implementable.
- Correction applied: the draft said the line-39 URL rule "sits under the `grounding_links` rules"; it is a standalone line after the per-confusion field list. Body text reworded; the conclusion (prose in inventory recommendations is not covered) stands. Also made the Learn link locale-explicit and named the mongosh install URL.
- Azure DocumentDB facts used (SRV connection string read from an env var, `--tlsAllowInvalidCertificates` only for the local Docker gateway) are consistent with the service; no connection string is written out.

### 3. Maintainer skeptic - confirmed
Names exact files and lines (`prompts/builder.md` step 3, `prompts/readiness_checker.md` lines 39 and 45) with replacement text, has an Azure DocumentDB angle (README guidance pointing at the DocumentDB Learn connect page, SRV string, local gateway TLS note) and removes measurable noise (114 recommendations). The optional HEAD-check and the environment install are clearly separated. Belongs in the harness repo, not the agent kit, MCP server or Learn.

## Finding ids

- F2697
- F2855
- F3085
- F3128
