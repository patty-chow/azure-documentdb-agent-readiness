---
title: "local-deployment: add a \"Not this\" line so agents stop reaching for the Azure Cosmos DB Emulator / port 10255"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 22
findings: 22
bucket: confusion-Q11
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# local-deployment: add a "Not this" line so agents stop reaching for the Azure Cosmos DB Emulator / port 10255

## What happens today

`skills/local-deployment/SKILL.md` and `local-choose-deployment-method.md` state the right answer in full: run `ghcr.io/documentdb/documentdb/documentdb-local:latest`, connect on **10260** with TLS and SCRAM-SHA-256. But nothing in the skill (or anywhere else in the kit) says what *not* to use. `grep -rniE 'emulator|cosmos|10255|8081|27017' skills/local-deployment` returns nothing, and `grep -rni emulator skills knowledge-base` also returns nothing.

That matters because the model's default is not "no idea", it is a specific wrong answer carried over from Azure Cosmos DB (NoSQL) and Azure Cosmos DB for MongoDB (RU): the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint `localhost:8081`, "Mongo endpoint on 10255"), sometimes with the claim that it "supports the MongoDB API". A skill that only asserts the positive answer does not displace that prior; a one-line disambiguation does.

Several other places in the kit reinforce the plain-MongoDB prior and contradict this skill:

- `skills/mcp-setup/SKILL.md` line 88, Step 2 table, option **B. Local MongoDB / DocumentDB** -> `mongodb://localhost:27017`
- `README.md` line 160 (`export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'`), mirrored in `GEMINI.md` line 27, `install.sh` lines 8/522/527, `install.ps1` lines 46/491 and `docs/installation/macos.md` line 21 ("Local DocumentDB / MongoDB: `mongodb://localhost:27017`")

## Why it matters

In an agent-readiness run of 100 Azure DocumentDB sample prompts (gpt-5-mini, this kit installed, DocumentDB + Azure + Learn MCP servers available), the cold-quiz question "How do you run the database locally for development and tests: which image or emulator, and which port?" was recorded as a confusion in all 120 run folders (100 samples plus reruns). 114 of those 120 cold answers named the Cosmos DB Emulator (97 distinct samples); 19 asserted port 10255. This PR is scoped to the 22 samples where the grader attributed the miss specifically to the emulator / 10255 carry-over and logged it as a finding.

Typical cold answers from the runs:

- "Use the Azure Cosmos DB Emulator ... connect to localhost with the Mongo port used by Cosmos (10255) and with TLS enabled."
- "Use the Azure Cosmos DB Emulator; SQL API at https://localhost:8081; Cosmos Mongo emulator endpoint common is 10255"

What is actually true: the Azure Cosmos DB Emulator emulates the Azure Cosmos DB service (its well-known endpoint is `localhost:8081`; the classic emulator can also expose an Azure Cosmos DB for MongoDB (RU) endpoint, port 10255 by default). It does not run the PostgreSQL-based DocumentDB engine behind the vCore Mongo gateway, so it exposes no `cosmosSearch` vector indexes (vector-ivf / vector-hnsw / vector-diskann), no DocumentDB text-search indexes, and not the gateway's TLS/SCRAM-SHA-256 behaviour. 10255 is the Cosmos DB for MongoDB (RU) port; Azure DocumentDB clusters are reached via a `mongodb+srv://...mongocluster.cosmos.azure.com/` string with no explicit port, and the local gateway listens on 10260. An agent that follows the cold answer either fails to connect or gets a local environment whose index commands and search behaviour diverge from the cluster, so integration tests pass locally and fail on Azure (or vice versa).

In the grounded pass, 109 of the 120 answers moved to the correct 10260 gateway answer, most often citing `documentdb-local-deployment` (57) or the Learn development-loop tutorial, so the content is right; it needs the negative statement so the skill is matched when the agent's query is phrased in emulator terms.

## Proposed change

### 1. `skills/local-deployment/SKILL.md`

Frontmatter `description`, append one clause:

```
... or diagnosing local connection problems. Also use when someone proposes the Azure Cosmos DB Emulator, port 10255/8081, or a stock mongo:* image for Azure DocumentDB local development -- those are not DocumentDB.
```

Under **Image choices**, add after the two bullets:

```markdown
- **Not this:** the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint 8081, MongoDB (RU) endpoint 10255) or a stock `mongo:*` image on 27017. The emulator serves Azure Cosmos DB (NoSQL and RU-based API for MongoDB) accounts, not Azure DocumentDB; neither runs the DocumentDB engine, so `cosmosSearch` vector indexes, DocumentDB text-search indexes and the gateway's TLS/SCRAM-SHA-256 behaviour will be missing or different. Port 10255 belongs to Cosmos DB for MongoDB (RU); Azure DocumentDB uses 10260 locally and no explicit port in the cloud `mongodb+srv://` string.
```

### 2. `skills/local-deployment/local-choose-deployment-method.md`

Add a row to the decision matrix and a second **Incorrect** block:

```markdown
| "Run it like Cosmos DB" (Azure Cosmos DB Emulator, port 10255) | **Do not.** The emulator is for Azure Cosmos DB accounts; use the Gateway image on 10260 |
```

````markdown
## Incorrect

Reaching for the Azure Cosmos DB Emulator or a plain MongoDB image because the service used to be called "Azure Cosmos DB for MongoDB vCore":

```bash
# Wrong product: emulates Azure Cosmos DB (NoSQL / RU API for MongoDB), not Azure DocumentDB
docker run -p 8081:8081 -p 10250-10255:10250-10255 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator

# Wrong engine: plain MongoDB, no cosmosSearch / DocumentDB text indexes
docker run -p 27017:27017 mongo:7
```

Neither exposes `cosmosSearch` vector indexes, DocumentDB text-search indexes, or the 10260 gateway's TLS + SCRAM-SHA-256 behaviour, so local tests do not predict cluster behaviour.
````

### 3. Consistency fixes (same PR, one line each)

- `skills/mcp-setup/SKILL.md` line 88, Step 2 option B: rename to **B. Local DocumentDB Gateway** and use `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` (link to `local-connection-config`).
- `README.md` line 160 and the mirrored defaults in `GEMINI.md`, `install.sh`, `install.ps1`, `docs/installation/macos.md`: replace `mongodb://localhost:27017` with the 10260 URI above, or label it explicitly as "plain MongoDB (not DocumentDB)".

Total diff is roughly 15 lines of Markdown plus a handful of one-line URI edits; no behaviour change to scripts beyond the default example URI and help text.

## Evidence (run folders from the readiness experiment; `02-readiness.json` -> `confusions[Q11]`)

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/02-readiness.json` -- cold answer names the emulator image and 10255
- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` -- emulator + "10255 for TLS in the cloud"
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json` -- emulator, 8081 and 10255 together
- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json` -- emulator "exposes the MongoDB-compatible endpoint on port 10255"
- `runs/02-ai-powered-product-recommendations/20261124-181835/02-readiness.json` -- emulator or stock Mongo on 27017

Kit state checked at commit `4f41c15` (2026-11-23).

## Verification

### 1. Already covered? -- confirmed (not covered)

- Agent kit clone at `4f41c15`: `grep -rniE 'emulator|cosmos|10255|8081|27017' skills/local-deployment` returns nothing; `grep -rni emulator skills knowledge-base` returns nothing. The skill only states the positive answer: "**Gateway** (`ghcr.io/documentdb/documentdb/documentdb-local:latest`) — MongoDB wire protocol on port **10260**" (`skills/local-deployment/SKILL.md`).
- The contradicting lines exist as described: `skills/mcp-setup/SKILL.md:88` "| **B. Local MongoDB / DocumentDB** | Local dev | `mongodb://localhost:27017` |"; `README.md:160`, `GEMINI.md:27`, `install.sh:8,522,527`, `install.ps1:46,491`, `docs/installation/macos.md:21`.
- Learn: https://learn.microsoft.com/en-us/azure/documentdb/development-loop shows the correct image and "The DocumentDB gateway endpoint is available on port `10260`" but does not mention or warn against the Cosmos DB Emulator. The DocumentDB TOC has no emulator/docker entry (only Azure Local and development-loop). Not in scope here, the fix target is the kit.
- documentdb-mcp: `docs/e2e-testing-guide.md` uses `documentdb-local` on 10260; no emulator anti-pattern guidance (and not the right repo for it).

### 2. Premise true? -- confirmed (with wording tightened)

- https://learn.microsoft.com/en-us/azure/cosmos-db/emulator: the emulator "emulates the Azure Cosmos DB service"; endpoint `localhost:8081`; Data Explorer "only supported in the API for NoSQL and API for MongoDB" (the RU-based API for MongoDB), provisioned-throughput/RU semantics. It is not Azure DocumentDB.
- https://learn.microsoft.com/en-us/azure/documentdb/development-loop: local DocumentDB is `ghcr.io/documentdb/documentdb/documentdb-local:latest` on 10260 with `tls=true&tlsAllowInvalidCertificates=true`.
- Azure DocumentDB facts (cosmosSearch vector indexes, DocumentDB text indexes, PostgreSQL-based engine, `mongocluster.cosmos.azure.com` SRV string with no explicit port) match the reference facts.
- Edits applied: the draft's stats paragraph was internally inconsistent ("108 of 117 wrong ... 112 of those named the emulator"); recomputed from the 120 run folders: Q11 confusion in 120/120, emulator named in 114 (97 samples), 10255 in 19. "Every one of the 22 runs produced the correct grounded answer" was not verifiable as stated; replaced with the measured 109/120 grounded answers citing 10260. Emulator description softened to say the classic emulator *can* expose a MongoDB (RU) endpoint on 10255 rather than implying it always does. MCP-setup replacement URI now includes `authMechanism=SCRAM-SHA-256` and placeholder credentials, matching `local-connection-config`. Fixed the nested code fence in item 2 (outer ```` fence). Listed exact line numbers for all 27017 occurrences. Removed the Claude Code footer from the issue body (attribution belongs in the PR description at submit time).

### 3. Maintainer skeptic -- confirmed

As a kit maintainer I would accept this: it names exact files and lines, gives the literal text to add, is DocumentDB-specific (Cosmos emulator vs DocumentDB gateway is precisely the product-rename confusion the kit exists to prevent), and fixes a real internal inconsistency (`mcp-setup` and README label 27017 "Local DocumentDB" while `local-deployment` says 10260). Small, low-risk Markdown diff. The install-script help text edits may be split to a follow-up if the maintainer prefers.

## Finding ids

- F0184
- F0461
- F1045
- F1079
- F1136
- F1406
- F1629
- F1722
- F1895
- F2022
- F2126
- F2330
- F2556
- F2688
- F2716
- F2751
- F2783
- F2811
- F2491
- F2980
- F3397
- F3503
