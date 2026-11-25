---
id: K23
title: "local-deployment: add a 'Not this' line steering agents away from the Azure Cosmos DB Emulator"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 22
member_drafts:
  - 030-believes-the-azure-cosmos-db-emulator-ports-8081-10250-10255.md
open_questions: 2
---

# local-deployment: add a "Not this" line steering agents away from the Azure Cosmos DB Emulator

## What happens today

`skills/local-deployment/SKILL.md` and `skills/local-deployment/local-choose-deployment-method.md` give the right answer: run `ghcr.io/documentdb/documentdb/documentdb-local:latest` and connect on port **10260** with TLS and SCRAM-SHA-256. Nothing in the skill, or anywhere else in the kit, says what *not* to use. `grep -rniE 'emulator|cosmos|10255|8081|27017' skills/local-deployment` returns nothing, and `grep -rni emulator skills knowledge-base` returns nothing (checked at commit `4f41c15`).

A coding agent's default answer is a specific wrong one, carried over from Azure Cosmos DB (NoSQL) and Azure Cosmos DB for MongoDB (RU): the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint `localhost:8081`; the classic emulator can also expose an Azure Cosmos DB for MongoDB (RU) endpoint, 10255 by default). A skill that only states the right answer does not displace that prior. A one-line disambiguation does, and it also lets the skill match a query written in emulator terms.

Several other kit files add to the problem by labelling plain MongoDB on 27017 as "local DocumentDB":

- `skills/mcp-setup/SKILL.md` line 88, Step 2 option **B. Local MongoDB / DocumentDB** -> `mongodb://localhost:27017`
- `README.md` line 160 (`export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'`), repeated in `GEMINI.md` line 27, `install.sh` lines 8/522/527, `install.ps1` lines 46/491 and `docs/installation/macos.md` line 21

## Why it matters

We gave gpt-5-mini 100 Azure DocumentDB sample-app prompts, with this kit installed and the DocumentDB, Azure and Learn MCP servers available. Before each build it answered a "cold" question without tools: "How do you run the database locally for development and tests: which image or emulator, and which port?" Nearly every sample answered wrongly. Most named the Cosmos DB Emulator, and some gave port 10255. This PR covers the **22 samples** where the grader traced the miss to the emulator or 10255 carry-over and logged it as a finding. All counts come from a single experiment run and from the cold quiz, which measures the model's priors rather than a defect in the kit's content; re-baseline after the harness fixes before quoting the number externally. A keyword recount of the findings file gives 23, so treat the number as approximate.

Typical cold answers:

- "Use the Azure Cosmos DB Emulator ... connect to localhost with the Mongo port used by Cosmos (10255) and with TLS enabled."
- "Use the Azure Cosmos DB Emulator; SQL API at https://localhost:8081; Cosmos Mongo emulator endpoint common is 10255"

The emulator emulates the Azure Cosmos DB service. It does not run the PostgreSQL-based open-source DocumentDB engine, so it has no `cosmosSearch` vector indexes (vector-ivf, vector-hnsw, vector-diskann), no DocumentDB text-search indexes and none of the gateway's TLS/SCRAM-SHA-256 behaviour. Port 10255 belongs to Cosmos DB for MongoDB (RU). Azure DocumentDB uses 10260 locally and a `mongodb+srv://...mongocluster.cosmos.azure.com/` string with no explicit port in the cloud. An agent that follows the cold answer either can't connect or gets a local environment whose indexes and search behaviour differ from the cluster's, so tests can pass locally and fail on Azure.

When the agent looked things up first, it mostly gave the correct 10260 gateway answer, often citing this skill. The content is right; it just needs the negative statement.

## Proposed change

### 1. `skills/local-deployment/SKILL.md`

Append to the frontmatter `description`:

```
... or diagnosing local connection problems. Also use when someone proposes the Azure Cosmos DB Emulator, port 10255/8081, or a stock mongo:* image for Azure DocumentDB local development -- those are not DocumentDB.
```

Under **Image choices**, add after the two existing bullets:

```markdown
- **Not this:** the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint 8081, MongoDB (RU) endpoint 10255) or a stock `mongo:*` image on 27017. The emulator serves Azure Cosmos DB (NoSQL and RU-based API for MongoDB) accounts, not Azure DocumentDB; neither runs the DocumentDB engine, so `cosmosSearch` vector indexes, DocumentDB text-search indexes and the gateway's TLS/SCRAM-SHA-256 behaviour will be missing or different. Port 10255 belongs to Cosmos DB for MongoDB (RU); Azure DocumentDB uses 10260 locally and no explicit port in the cloud `mongodb+srv://` string.
```

### 2. `skills/local-deployment/local-choose-deployment-method.md`

Add a row to the decision matrix:

```markdown
| "Run it like Cosmos DB" (Azure Cosmos DB Emulator, port 10255) | **Do not.** The emulator is for Azure Cosmos DB accounts; use the Gateway image on 10260 |
```

Add a second **Incorrect** block:

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

### 3. Consistency fixes (one line each)

- `skills/mcp-setup/SKILL.md` line 88, Step 2 option B: rename it **B. Local DocumentDB Gateway**, use `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` and link to `local-connection-config`.
- `README.md` line 160, `GEMINI.md` line 27, `install.sh` lines 8/522/527, `install.ps1` lines 46/491, `docs/installation/macos.md` line 21: replace `mongodb://localhost:27017` with the 10260 URI above, or label it explicitly as "plain MongoDB (not DocumentDB)".

That is about 15 lines of Markdown plus a few one-line edits to example URIs. Script behaviour does not change beyond the default example URI and help text.

## Evidence

In each run folder, see `02-readiness.json` -> `confusions[Q11]`:

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/`: the cold answer names the emulator image and 10255
- `runs/16-loyalty-points-ledger/20261124-184937/`: the emulator, plus "10255 for TLS in the cloud"
- `runs/15-cohort-analysis-backend/20261124-205336/`: the emulator, 8081 and 10255 together
- `runs/20-store-locator-with-geospatial-search/20261124-185729/`: the emulator "exposes the MongoDB-compatible endpoint on port 10255"
- `runs/02-ai-powered-product-recommendations/20261124-181835/`: the emulator, or stock Mongo on 27017

## Open questions

1. Should the install-script and README edits in section 3 stay in this PR or move to a follow-up? They change user-facing default example URIs. (Maintainer preference.)
2. The same 27017 "local URI" also appears in the microsoft/documentdb-mcp README. That is out of scope here and should be tracked as its own item. Can the maintainers confirm that the two repositories should use the same 10260 gateway example?

The reviewer's list of claims needing SME confirmation (change-stream limits, retryWrites, error codes, driver floors, HNSW/IVF limits) does not apply to this PR. The emulator description was checked against the Learn emulator page, and the 10260 gateway details against the Learn development-loop page.

## Source drafts

- 030-believes-the-azure-cosmos-db-emulator-ports-8081-10250-10255.md
