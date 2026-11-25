---
title: "Add a driver compatibility and client-options page for Azure DocumentDB (supported driver versions, read/write concern mapping, retry and pool/timeout guidance)"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 10
findings: 10
bucket: learn-practice_not_public
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Learn feedback: add a driver compatibility and client-options reference for Azure DocumentDB

**Pages affected:** https://learn.microsoft.com/en-us/azure/documentdb/ — the FAQ (https://learn.microsoft.com/en-us/azure/documentdb/faq), the MongoDB feature-compatibility page (https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features), the service limits page (https://learn.microsoft.com/en-us/azure/documentdb/limitations), the high availability page (https://learn.microsoft.com/en-us/azure/documentdb/high-availability), and the driver quickstarts for Node.js, Python, Java, .NET and Go.

## What happens today
Coding agents building Azure DocumentDB (vCore) apps look for four facts on Learn. Some pieces exist, but they are spread across pages and do not form a reference an agent can cite:

1. **Supported driver versions.** The FAQ says the service supports MongoDB wire protocol versions 5.0, 6.0, 7.0 and 8.0 and that "any driver that supports the MongoDB wire protocol connects". The Mongoose quickstart and tutorial have a "Tested driver version" section (MongoDB Node.js driver 7.8.0 via Mongoose 9.12.1) and pin `mongoose@9.12.1`. No other quickstart (Node.js `mongodb`, PyMongo, Java, .NET, Go) states a tested or minimum driver version, and no page gives a per-language table. Agents pin a version (for example `pymongo==4.5.0`) but cannot confirm it is supported. One audit records searches for "Azure DocumentDB supported pymongo driver versions" and "DocumentDB wire protocol driver compatibility" that found no table.
2. **Read/write concern mapping.** No page says how `writeConcern` (`w: 1`, `w: "majority"`, `j: true`), `readConcern` and `readPreference` behave on a vCore cluster. The high availability page says the primary and standby shards use synchronous replication with zero data loss on failover, but it does not tie that to the concern values a driver sends. Agents building ledgers and status dashboards either assume MongoDB replica-set defaults or add hedge comments.
3. **Retry and legacy options.** The portal connection string and the driver quickstarts include `retrywrites=false`, and the Agent Kit says retryable writes are not supported, but the Mongoose tutorial says that setting is "a sample, not a statement that Azure DocumentDB requires retryable writes to be disabled". No page settles whether retryable writes are supported. No note says that `useNewUrlParser`/`useUnifiedTopology` do nothing in current drivers, so agents add them or argue about removing them.
4. **Pool and timeout defaults.** Most quickstarts show a bare `MongoClient(connectionString)`. The Mongoose tutorial uses `maxPoolSize: 10` and `serverSelectionTimeoutMS: 30000` without explaining them. No page gives recommended `maxPoolSize`, `minPoolSize`, `serverSelectionTimeoutMS` or `socketTimeoutMS` values per hosting model.

## Why it matters
10 of 100 samples (10 findings) hit this. 3 audits marked "The driver version is pinned and is one the service supports" as **listed_not_found** because no public per-driver source exists to check against. 7 more fell back to **prior_knowledge_only** for concern levels, driver options and pool tuning. As a result, apps shipped with unverified driver pins, concern settings copied from generic MongoDB guidance (including on a points ledger that relies on `w: "majority"` durability), and arbitrary pool and timeout numbers.

## Proposed change
Add a section titled **"Driver compatibility and recommended client options"**. It can be a new page linked from every driver quickstart and from the FAQ answer "Are MongoDB drivers and tools compatible with Azure DocumentDB?", or a section of the existing feature-compatibility page. It should contain:

- **Driver table:** one row per language/driver (Node.js `mongodb`, Mongoose, PyMongo, Java, .NET, Go), with the minimum supported version for each wire protocol / `serverVersion` (5.0, 6.0, 7.0, 8.0), the version the docs team tested (reuse the "Tested driver version" pattern already in the Mongoose quickstart), and a pinned install line (for example `npm install mongodb@<x.y.z>` or `pymongo==<x.y.z>`).
- **Consistency table:** each `writeConcern` (`w: 1`, `w: "majority"`, `j`), `readConcern` (`local`, `majority`, `linearizable`/`snapshot` if applicable) and `readPreference` mode, with what the service does with it (honored, accepted but ignored, or rejected), for clusters with and without in-region high availability and for replica clusters. Link the synchronous-replication statement on the high availability page.
- **Options note:** `useNewUrlParser` and `useUnifiedTopology` have no effect in Node.js driver 4+ and were removed in Mongoose 6+, so remove them. State plainly whether retryable writes are supported and whether `retrywrites=false` (as in the portal connection string) is required or only recommended, so the quickstarts, the Mongoose tutorial and the Agent Kit can say the same thing.
- **Pool and timeout table:** recommended `maxPoolSize`, `minPoolSize`, `serverSelectionTimeoutMS`, `socketTimeoutMS` and `maxIdleTimeMS` (the portal string uses `maxIdleTimeMS=120000`) for serverless/Functions, App Service/containers and batch jobs.
- **One sentence on pinning:** pin the tested driver version and commit `package-lock.json` / `requirements.txt`.

Related: the Agent Kit `skills/connection/SKILL.md` already has a pool-sizing table, but its sample URI uses `retryWrites=true`, as do `skills/driver/driver-singleton-client.md` and `skills/security/security-tls-required.md`, while `skills/azure-deployment/SKILL.md` says retryable writes are not supported. A Learn page would give the kit an authoritative source to cite and would settle that inconsistency.

## Evidence
- runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json (driver pin listed_not_found; search terms recorded)
- runs/13-algorithmic-trade-journal/20261124-191835/05-audit.json (driver pin listed_not_found)
- runs/11-market-news-sentiment-orchestration/20261124-191425/05-audit.json (driver pin listed_not_found)
- runs/16-loyalty-points-ledger/20261124-184937/05-audit.json (writeConcern semantics for a ledger, prior knowledge only)
- runs/09-inventory-reorder-multi-agent-system/20261124-184020/05-audit.json (readConcern/writeConcern mapping, prior knowledge only)

## Verification

### 1. Already covered? — partially_covered
Some of the ask is on Learn, but scattered and incomplete:
- https://learn.microsoft.com/en-us/azure/documentdb/faq: "Azure DocumentDB supports MongoDB wire protocol versions 5.0, 6.0, 7.0, and 8.0" and "Any driver that supports the MongoDB wire protocol connects to Azure DocumentDB". This covers server versions, not per-driver minimum or tested versions.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-mongoose and https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose: a "Tested driver version" section (Node.js driver 7.8.0 via Mongoose 9.12.1), `npm install mongoose@9.12.1`, and `maxPoolSize: 10` / `serverSelectionTimeoutMS: 30000` in sample code. Only Mongoose has this. The quickstart-nodejs, quickstart-python, quickstart-java and quickstart-go pages show only the connection string (with `retrywrites=false&maxIdleTimeMS=120000`) and no version or pool guidance.
- https://learn.microsoft.com/en-us/azure/documentdb/high-availability: primary and standby shards "use synchronous replication" and failover is "zero data loss". No mapping to writeConcern/readConcern/readPreference.
- https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features and https://learn.microsoft.com/en-us/azure/documentdb/limitations: nothing on driver versions, concern levels, retryable writes or pool/timeouts.
- Agent Kit: `skills/connection/SKILL.md` has pool/timeout tables (for example `serverSelectionTimeoutMS` 5s, `socketTimeoutMS` 30s for OLTP), but no driver version or concern guidance. `skills/driver/SKILL.md` has only the singleton rule. No kit file mentions readConcern or writeConcern.
A per-language driver table, a concern mapping table, and a settled retryable-writes statement are not documented anywhere.

### 2. Is the premise true? — confirmed (wording corrected)
The central gap is real. Corrections applied to the body:
- The original said Learn has "no single citable statement" of driver support. In fact, the FAQ gives the supported wire protocol versions and the Mongoose pages give a tested driver version. The body now says what exists and asks for a per-language table.
- The original called `retrywrites=false` a "required" URI option. The Mongoose tutorial explicitly says it is "not a statement that Azure DocumentDB requires retryable writes to be disabled", while the kit's azure-deployment skill says retryable writes are not supported. The body now asks Learn to settle this rather than asserting it is required.
- Checked and kept: `useNewUrlParser`/`useUnifiedTopology` have no effect from Node.js driver 4.0 and were removed in Mongoose 6 (Mongoose 6 migration guide; Node.js driver 4.0 release notes). The kit's `skills/connection/SKILL.md` line 60 does use `retryWrites=true`, as do `skills/driver/driver-singleton-client.md` line 26 and `skills/security/security-tls-required.md` line 26.
- The evidence files exist and contain the cited listed_not_found driver-pin requirements and the prior-knowledge-only writeConcern notes.

### 3. Maintainer skeptic — confirmed
It names specific Learn pages (FAQ, compatibility-features, limitations, high-availability, the driver quickstarts) and a concrete deliverable (four tables plus one pinning sentence). Its angle is specific to Azure DocumentDB: how the service treats concern levels on a PostgreSQL-based engine with synchronous HA, which drivers it supports, and the open contradiction over retryable writes across Learn pages and the kit. A docs maintainer would accept this as a content request. Behaviour per concern value has to come from the product team, but the request is clear about what is needed.

## Finding ids
- F1327
- F1464
- F1427
- F0202
- F1852
- F2142
- F2767
- F2238
- F2677
- F2707
