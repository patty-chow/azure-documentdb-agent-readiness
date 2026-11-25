---
id: K24
title: "mcp-setup skill, README and installers: stop presenting a localhost URI as the default"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 5
member_drafts:
  - 031-agent-kit-itself-reinforces-the-27017-prior-mcp-setup-skill-.md
open_questions: 2
---

# mcp-setup skill, README and installers: stop presenting a localhost URI as the default

## What happens today

Nine lines in six files give `mongodb://localhost:27017` (port 27017, no TLS) as the connection string for a local DocumentDB:

| File | Line(s) | Current text |
|---|---|---|
| `skills/mcp-setup/SKILL.md` | 88 | Step 2 table, row **B. Local MongoDB / DocumentDB**: `mongodb://localhost:27017` |
| `README.md` | 160 | `export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'` |
| `GEMINI.md` | 27 | same export |
| `docs/installation/macos.md` | 21 | `**Local DocumentDB / MongoDB:** mongodb://localhost:27017` |
| `install.sh` | 8, 522, 527 | usage comment, `for local dev:` hint, `Local:` example |
| `install.ps1` | 46, 491 | `.EXAMPLE` block, `Local:` example |

The local DocumentDB gateway container (`ghcr.io/documentdb/documentdb/documentdb-local`) listens on **10260** and requires **TLS** (self-signed certificate) and **SCRAM-SHA-256**. The kit already says this correctly in `skills/local-deployment/` (`SKILL.md:11`, `local-env-driven-config.md:61`) and in the README Quickstart, which starts the container with `-p 10260:10260` at `README.md:49`. So the README starts the container on 10260 and, 110 lines later, tells the MCP server to connect on 27017. An MCP profile pointed at 27017 without TLS cannot reach that container. The Microsoft Learn tutorial `azure/documentdb/development-loop` uses the same 10260 + TLS endpoint.

## Why it matters

In one run of an agent-readiness experiment (100 Azure DocumentDB sample app prompts, an agent using this kit's skills plus the DocumentDB, Azure and Learn MCP servers), **5 of the 100 samples** produced findings about this risk. Counts are from that single run.

- Asked cold how to run the database locally, the agent typically answered "`mongo:7` on 27017". The kit is meant to correct that prior. But `mcp-setup` is often loaded before `local-deployment`, and its row B confirms the wrong answer.
- Generated apps then wired `.env.example`, seed scripts and integration tests to a stock `mongo` image on 27017. Outside the five samples above, other runs show the same thing: a test defaulting to `localhost:27017` and an `.env.example` hard-coding `:27017`. Against plain MongoDB, these apps lose parity for `cosmosSearch` vector indexes (vector-ivf, vector-hnsw, vector-diskann), text search and TLS/SCRAM behavior, so tests pass or fail for the wrong reasons.

## Proposed change

This PR changes documentation only. The installers only print these strings, so no code paths change.

**1. `skills/mcp-setup/SKILL.md`, Step 2 table (lines 85-89).** Replace the table and add a note under it:

```markdown
| Option | When to use | Example URI |
|---|---|---|
| **A. Azure DocumentDB** | Production / cloud dev | `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` |
| **B. Local DocumentDB (gateway container)** | Local dev with feature parity | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` |
| **C. Custom MongoDB-compatible** | Atlas, self-hosted, third-party | `mongodb://<user>:<pw>@host:port/?tls=true` |
| **D. Plain MongoDB (not DocumentDB)** | Driver-only smoke tests | `mongodb://localhost:27017` |

The local DocumentDB gateway listens on **10260**, not 27017. It uses a self-signed
TLS certificate and SCRAM-SHA-256. `tlsAllowInvalidCertificates=true` is only for that
local certificate. Never put it in a cloud profile. A plain `mongo` image on 27017
does not reproduce DocumentDB vector or text indexes, or its TLS/SCRAM behavior. See
the `documentdb-local-deployment` skill for the container and docker-compose setup.
```

(Row A now uses the full Azure portal connection-string format, including `retrywrites=false&maxIdleTimeMS=120000`. The existing row leaves out those two parameters.)

**2. `README.md` line 160 and `GEMINI.md` line 27.** Replace the export:

```bash
export DOCUMENTDB_CONNECTION_PROFILES='{"local":{"uriEnv":"DOCUMENTDB_LOCAL_URI"}}'
# local gateway: port 10260, TLS with a self-signed cert (dev only)
export DOCUMENTDB_LOCAL_URI='mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true'
```

**3. `docs/installation/macos.md` line 21.** Replace it with two bullets:

```markdown
- **Local DocumentDB (gateway container):** `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`
- **Plain MongoDB / Atlas / self-hosted:** your standard MongoDB URI (e.g. `mongodb://localhost:27017`).
```

**4. `install.sh` lines 8, 522, 527.**

```bash
#   curl -fsSL .../install.sh | bash -s -- --uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" --yes
...
    err "for local DocumentDB: --uri \"mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true\""
...
  log "  • Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
  log "  • Plain MongoDB:    mongodb://localhost:27017"
```

**5. `install.ps1` lines 46, 491.**

```powershell
    .\install.ps1 -Uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" -Yes
...
    Write-Host "  - Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
    Write-Host "  - Plain MongoDB:    mongodb://localhost:27017"
```

After the change, `grep -rn 27017` should match only lines explicitly labeled plain MongoDB.

Out of scope for this PR: `microsoft/documentdb-mcp` has the same pattern in its `README.md` (lines 73, 95, 115 and 231, plus the VS Code install badge on line 1) and `.env.example:36`. That needs a separate issue in that repository. No draft for it exists yet.

## Evidence

Run folders from the experiment:

- `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json`: cold answer `mongo:7` on 27017
- `runs/04-regulatory-reporting-orchestration/20261124-200545/02-readiness.json`: same confusion
- `runs/05-churn-prediction-pipeline/20261124-203754/02-readiness.json`: same confusion; the agent later grounded itself on the Learn `development-loop` page (10260)
- `runs/09-lead-scoring-agent/20261124-204408/` (`02-readiness.json`, `events.jsonl`): same confusion, and the run loaded `documentdb-mcp-setup`
- `runs/13-chronic-disease-risk-predictor/20261124-194916/app/tests/test_seed.py`: the shipped test defaults to `localhost:27017`
- `runs/12-cross-border-payment-audit-trail/20261124-201744/app/.env.example`: the shipped URI uses `:27017`

## Open questions

1. Row A uses the Azure portal connection-string format, which includes `retrywrites=false`. Drafts from this experiment disagree on why: some say retryable writes are unsupported or cause write errors on Azure DocumentDB, others say Learn makes no such claim. This PR adds no rationale text, but please confirm the engineering answer before any explanation is written. Also confirm whether the local gateway URI (row B and the exports) needs `retrywrites=false`. [needs SME confirmation]
2. Should the local gateway URI also set `authMechanism=SCRAM-SHA-256` explicitly? `local-env-driven-config.md:61` sets it. The Learn `development-loop` tutorial and the strings above do not. Please name one canonical local URI so every file in the kit uses it. [needs SME confirmation]

## Source drafts

- 031-agent-kit-itself-reinforces-the-27017-prior-mcp-setup-skill-.md
