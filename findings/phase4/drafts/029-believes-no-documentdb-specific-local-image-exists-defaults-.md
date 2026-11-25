---
title: "Q11 local-dev confusion (stock mongo on 27017 instead of documentdb-local on 10260) is a model prior already corrected - no action"
repo: learn-docs
type: note-only
status: drop
priority: P3
sample_count: 72
findings: 76
bucket: confusion-Q11
verdicts:
  skipped: note-only
---

# Note: Q11 local-dev confusion is a model prior already corrected by the Agent Kit and Learn — no issue/PR filed

## What happens today

When asked cold "How do you run the database locally for development and tests: which image or emulator, and which port?", gpt-5-mini answered wrongly or partly wrongly in 76 runs covering 72 of the 100 samples:

- 49 answers: run a stock MongoDB container (`mongo:6.0`, `mongo:7.0`, `mongo:latest`) on 27017 with no TLS, "there is no DocumentDB emulator".
- 23 answers: build open-source DocumentDB from source or run a generic Postgres + extension container; a few half-recalled a container image but got port/TLS wrong.
- 4 answers: Cosmos DB emulator does not cover it, so test against the live cluster (incurring cost).

The correct answer: `ghcr.io/documentdb/documentdb/documentdb-local:latest`, MongoDB wire protocol on **10260** (PostgreSQL on 9712), TLS with a self-signed certificate (`tlsAllowInvalidCertificates=true`, dev only) and SCRAM-SHA-256, with `SKIP_INIT_DATA` / `INIT_DATA_PATH` seeding. It is the only local target that exposes cosmosSearch vector indexes, DocumentDB text-search indexes and the gateway's TLS/auth behaviour; a stock mongo container gives false confidence.

## Why no change is proposed

The readiness stage measures the prior *before* the model reads any skill or doc. Once grounded, every one of the 76 runs produced the right answer, citing one of two existing sources:

1. **Agent Kit** `skills/local-deployment/SKILL.md` and its pages: `local-choose-deployment-method.md` (decision matrix; exact `docker run --pull always -dt -p 10260:10260 ... documentdb-local:latest`; "Start with the prebuilt Gateway image; drop down to source only when you must modify the engine"), `local-connection-config.md` (10260, `--tls`, `--tlsAllowInvalidCertificates`, SCRAM-SHA-256), `local-sample-data-management.md` (`SKIP_INIT_DATA` / `INIT_DATA_PATH`), `local-prod-parity.md` (compose snippet; "Integration tests target the local Gateway container, not an in-memory MongoDB").
2. **Learn** https://learn.microsoft.com/en-us/azure/documentdb/development-loop — "Start the container" gives `docker pull` / `docker run --publish 10260:10260` and the `localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` connection-string format.

Across all 117 run folders, no generated app uses a stock `image: mongo:` container; the few `27017` strings are placeholder URIs in `.env.example` or test defaults, not a local-dev recommendation. The findings' proposed "add a local-dev section to the quickstart / sample README" would not change the cold score, which is what they were derived from.

## Optional low-priority polish (not filed)

- **Learn**: `quickstart-nodejs` and `quickstart-python` have no link to `development-loop` and never mention docker or 10260. A one-line "Develop locally first: Tutorial: Build a TypeScript app with DocumentDB and deploy to Azure" entry under *Related content* would route agents and humans to the local container before they reach for `mongo:7`.
- **Agent Kit** `skills/local-deployment/local-prod-parity.md`: add a short local-gateway-vs-Azure feature table (cosmosSearch vector-ivf/hnsw/diskann, text-search indexes, Entra ID auth, HA/replicas, sharding) — asked for in F3463; the page explains parity in prose only.

## Evidence (run folders)

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` — confusions[Q11]: cold "official MongoDB docker image on 27017"; grounded cites the local-deployment skill, 10260.
- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json` — cold `docker run -p 27017:27017 mongo:7.0`; grounded cites development-loop; F3463 matrix request.
- `runs/10-drug-formulary-semantic-search/20261124-194440/02-readiness.json` — cold "mongo:7 on 27017, use live cluster for vector"; grounded names image, 10260, TLS, SCRAM-SHA-256.
- `runs/18-sanctions-list-screening-agent/20261124-202645/02-readiness.json` — F3115 "differences from vanilla mongo" request, already covered by local-prod-parity.md.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/05-audit.json` — post-build doc_gap restating that mongo:latest on 27017 is not a parity substitute.

## Skip reason

Model-prior-no-fix. The 76 Q11 confusions are cold (pre-grounding) answers reflecting Atlas/Community-Server and Cosmos DB RU-era training data. Both the Agent Kit documentdb-local-deployment skill (SKILL.md + local-choose-deployment-method.md, local-connection-config.md, local-sample-data-management.md, local-prod-parity.md) and the Learn development-loop tutorial already state the image, port 10260, TLS/SCRAM and seed vars exactly, and every grounded answer in these runs landed on them; no generated app used a stock mongo container. The findings' proposed quickstart/README additions would not change the cold score. Only optional low-priority polish remains (cross-link development-loop from quickstart-nodejs/python Related content; a feature-parity table in local-prod-parity.md), noted in the draft body but not worth a standalone issue.

## Verification

- skipped: note-only. The drafter decided no action is warranted; covered/premise/maintainer checks were not run. The skip reason is strong: the confusion is measured before grounding, and every grounded answer reached the correct image and port from the existing Agent Kit local-deployment skill or the Learn development-loop tutorial.

## Finding ids

- F0009
- F0045
- F0076
- F0113
- F0153
- F0219
- F0263
- F0291
- F0320
- F0354
- F0391
- F0500
- F0530
- F0562
- F0602
- F0633
- F0700
- F0730
- F0798
- F0829
- F0852
- F0922
- F0948
- F1005
- F1107
- F1166
- F1203
- F1229
- F1264
- F1303
- F1342
- F1375
- F1439
- F1492
- F1661
- F1687
- F1794
- F1865
- F1926
- F1956
- F1987
- F2088
- F2157
- F2221
- F2248
- F2293
- F2393
- F2430
- F2464
- F2522
- F2624
- F2653
- F2846
- F2880
- F2945
- F3018
- F3046
- F1593
- F1758
- F1831
- F2057
- F2190
- F2363
- F2595
- F2913
- F3077
- F3230
- F3262
- F3302
- F3327
- F3430
- F3463
- F3115
- F3149
- F3181
- F3364
