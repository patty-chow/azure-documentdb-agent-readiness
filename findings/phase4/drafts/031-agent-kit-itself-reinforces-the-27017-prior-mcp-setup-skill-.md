---
title: "mcp-setup skill, README, GEMINI.md, macOS install doc and install.sh/install.ps1 present mongodb://localhost:27017 as the local DocumentDB URI; should be the 10260 + TLS gateway URI"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 5
findings: 5
bucket: confusion-Q11
verdicts: |
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# mcp-setup skill, README, GEMINI.md and the installers give `mongodb://localhost:27017` as the local DocumentDB URI; should be the 10260 + TLS gateway URI

## What happens today

Nine lines in six files of the kit present port 27017 with no TLS as the connection string for a *local DocumentDB*:

| File | Line | Current text |
|---|---|---|
| `skills/mcp-setup/SKILL.md` | 88 | `**B. Local MongoDB / DocumentDB** \| Local dev \| mongodb://localhost:27017` |
| `README.md` | 160 | `export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'` (under "Local / sandbox SCRAM") |
| `GEMINI.md` | 27 | same export |
| `docs/installation/macos.md` | 21 | `**Local DocumentDB / MongoDB:** mongodb://localhost:27017` |
| `install.sh` | 8, 522, 527 | usage comment, `for local dev:` hint and `"Local:  mongodb://localhost:27017"` example |
| `install.ps1` | 46, 491 | `.EXAMPLE` block and `"  - Local:  mongodb://localhost:27017"` example |

The local DocumentDB gateway (`ghcr.io/documentdb/documentdb/documentdb-local`) listens on **10260** and requires **TLS** (self-signed certificate) and **SCRAM-SHA-256**. The kit already says so, correctly, in `skills/local-deployment/SKILL.md`, `local-connection-config.md`, `local-ports-and-bindings.md`, `local-env-driven-config.md` (line 61) and in the README's own Quickstart (`README.md:49` runs the container with `-p 10260:10260`). The README is therefore internally inconsistent: it starts the container on 10260 at line 49 and tells the MCP server to connect on 27017 at line 160. Pointing the MCP server at 27017 with no TLS simply fails against that container.

## Why it matters

In an "agent readiness" experiment over 100 Azure DocumentDB sample prompts (gpt-5-mini, Agent Kit skills + DocumentDB/Azure/Learn MCP servers):

- The cold-quiz question "how do you run the database locally, which image and port?" was answered wrong or partly wrong in most samples; the typical cold answer was `mongo:7` on `27017`. The kit's job is to correct that prior.
- About 28 run event logs reference `mcp-setup`, some loading it before `local-deployment`. An agent that reads row B of the Step 2 table gets its 27017/no-TLS belief **confirmed by the kit** before `local-deployment` gets a chance to correct it.
- Generated apps shipped the wrong port: `runs/13-chronic-disease-risk-predictor/.../app/tests/test_seed.py` defaults to `localhost:27017`, and `runs/12-cross-border-payment-audit-trail/.../app/.env.example` hard-codes `:27017`. Against a plain `mongo` container those apps lose parity for `cosmosSearch` vector indexes, text search and TLS/SCRAM behaviour, which is the build risk the five findings below call out.

The five findings in this bucket (samples 03, 04, 05, 06, 09) all state the same risk: builders wiring `.env.example`, seed scripts and integration tests to a stock `mongo:7` on 27017 and getting false positives/negatives.

## Proposed change

**1. `skills/mcp-setup/SKILL.md`, Step 2 table (lines 85-89).** Separate "local DocumentDB" from "plain MongoDB" and give the real local URI:

```markdown
| Option | When to use | Example URI |
|---|---|---|
| **A. Azure DocumentDB** | Production / cloud dev | `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256` |
| **B. Local DocumentDB (gateway container)** | Local dev with feature parity | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` |
| **C. Custom MongoDB-compatible** | Atlas, self-hosted, third-party | `mongodb://<user>:<pw>@host:port/?tls=true` |
| **D. Plain MongoDB (not DocumentDB)** | Driver-only smoke tests | `mongodb://localhost:27017` |

The local DocumentDB gateway listens on **10260**, not 27017, with a self-signed
TLS certificate and SCRAM-SHA-256. `tlsAllowInvalidCertificates=true` is for that
local certificate only; never put it in a cloud profile. A plain `mongo` image on
27017 does not reproduce DocumentDB vector/text indexes or TLS/SCRAM behaviour; see
the `documentdb-local-deployment` skill for the container and docker-compose setup.
```

**2. `README.md` line 160 and `GEMINI.md` line 27.** Replace the export so it matches the Quickstart container at `README.md:49`:

```bash
export DOCUMENTDB_CONNECTION_PROFILES='{"local":{"uriEnv":"DOCUMENTDB_LOCAL_URI"}}'
# local gateway: port 10260, TLS with a self-signed cert (dev only)
export DOCUMENTDB_LOCAL_URI='mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true'
```

**3. `docs/installation/macos.md` line 21.** Change to two bullets:

```markdown
- **Local DocumentDB (gateway container):** `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`
- **Plain MongoDB / Atlas / self-hosted:** your standard MongoDB URI (e.g. `mongodb://localhost:27017`).
```

**4. `install.sh` lines 8, 522 and 527.** Update the usage comment and the hints:

```bash
#   curl -fsSL .../install.sh | bash -s -- --uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" --yes
...
    err "for local DocumentDB: --uri \"mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true\""
...
  log "  • Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
  log "  • Plain MongoDB:    mongodb://localhost:27017"
```

**5. `install.ps1` lines 46 and 491.** Same change for Windows:

```powershell
    .\install.ps1 -Uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" -Yes
...
    Write-Host "  - Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
    Write-Host "  - Plain MongoDB:    mongodb://localhost:27017"
```

No code paths change; the installers only print these strings. A `grep -rn 27017` after the change should hit only the rows explicitly labelled plain MongoDB.

Related (separate repo, not part of this PR): `microsoft/documentdb-mcp` has the same pattern in `README.md` (lines 73, 95, 115, 231, and the VS Code install badge description) and `.env.example:36`; a matching issue should be filed there.

## Evidence (run folders from the experiment)

- `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json`: confusions Q11, cold answer `mongo:7` on 27017
- `runs/04-regulatory-reporting-orchestration/20261124-200545/02-readiness.json`: confusions Q11
- `runs/05-churn-prediction-pipeline/20261124-203754/02-readiness.json`: confusions Q11, grounded via Learn `development-loop` page (10260)
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json` + `events.jsonl`: confusions Q11; same run loaded `documentdb-mcp-setup`
- `runs/13-chronic-disease-risk-predictor/20261124-194916/app/tests/test_seed.py`: shipped `localhost:27017` default
- `runs/12-cross-border-payment-audit-trail/20261124-201744/app/.env.example`: shipped `:27017` URI

## Verification

### 1. Already covered? partially_covered
The correct local URI is documented in the kit, but only in the `local-deployment` skill and the README Quickstart docker run. The MCP-setup path (skill, README MCP section, GEMINI.md, macOS install doc, both installers) still gives 27017. So the correct fact exists but not where the MCP-setup path sends the agent, and the two places contradict each other. Nothing in the kit fixes the 27017 rows.
- `skills/local-deployment/local-env-driven-config.md:61`: `DOCUMENTDB_URI=mongodb://<username>:<password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256`
- `skills/local-deployment/SKILL.md:11`: "Gateway ... MongoDB wire protocol on port **10260**."
- `README.md:49`: `docker run ... -p 10260:10260`
- Still wrong (grep `27017`): `skills/mcp-setup/SKILL.md:88`, `README.md:160`, `GEMINI.md:27`, `docs/installation/macos.md:21`, `install.sh:8,522,527`, `install.ps1:46,491`.
- Correction applied: the draft listed seven places and missed `install.ps1:46,491`; added as change 5 and the count fixed to nine lines in six files.

### 2. Premise true? confirmed
The Learn tutorial https://learn.microsoft.com/en-us/azure/documentdb/development-loop (updated 2026-11-23) runs `ghcr.io/documentdb/documentdb/documentdb-local:latest` with `--publish 10260:10260` and states "The DocumentDB gateway endpoint is available on port `10260`", with connection string `mongodb://<admin-username>:<admin-password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`. That matches the kit's own local-deployment skill. Port 27017 is the stock MongoDB default and is not used by the DocumentDB local gateway. Evidence files cited in the draft exist and contain `27017`. Corrections applied: the draft's exact counts (62/30 of 101, 104 of 120, 27 runs, 4 apps) could not be re-derived here; the 27 figure became "about 28 run event logs reference mcp-setup" (from a grep of `events.jsonl`), and the other counts were softened to qualitative statements backed by the cited files.

### 3. Maintainer skeptic: confirmed
Small, concrete docs-only PR with exact file/line targets and replacement text, fixing an internal contradiction in the kit (README line 49 vs line 160) and clearly DocumentDB-specific. I would accept it. The same pattern in `microsoft/documentdb-mcp` README is out of scope for this repo and is called out as a separate follow-up.

## Finding ids

- F0426
- F0664
- F0769
- F0974
- F1527
