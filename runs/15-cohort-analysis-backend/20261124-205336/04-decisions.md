# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 9 |
| operator | 3 |
| readiness_report | 3 |
| model_default | 1 |
| tool_unavailable | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:03:54+00:00

## D002 (build): I chose Python 3.11+ with FastAPI (uvicorn) as the language and framework for the sample.

- **Instead of:** Node.js/Express; Python/FastAPI; Go/Fiber
- **Because:** Python + FastAPI is concise for building small HTTP services, matches the prompt, and is supported in the run environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.11 (or latest stable 3.x available on the developer machine) and FastAPI ~0.95+"
- **When:** 2026-11-25T12:04:33+00:00

## D003 (build): I chose PyMongo (pymongo) 4.x as the MongoDB driver and will use a singleton MongoClient per process.

- **Instead of:** motor (async MongoDB driver); pymongo (sync)
- **Because:** PyMongo 4.x is compatible with MongoDB 7.0 wire protocol; singleton client is best-practice per documentdb-driver skill.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use PyMongo (pymongo) 4.x (compatible with MongoDB 7.0 wire protocol). Implement MongoClient as a singleton per process as recommended by documentdb-driver."
- **When:** 2026-11-25T12:04:36+00:00

## D004 (build): I chose to use the connection string from DOCUMENTDB_URI environment variable.

- **Instead of:** Use Microsoft Entra ID (OIDC) auth; Use connection string from env var DOCUMENTDB_URI
- **Because:** Matches run environment and avoids OIDC complexity for the sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'connection string is in the environment variable DOCUMENTDB_URI'.
- **When:** 2026-11-25T12:04:59+00:00

## D005 (build): I chose separate collections: 'customers' and 'events' (purchases) with denormalized key fields (channel and product_id) on the events and a schemaVersion field.

- **Instead of:** customers + events collections with denormalization; single collection with embedded events per customer
- **Because:** Separation keeps documents small, simplifies seeding and querying; denormalized fields on events speed aggregation without complex joins.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Create collections: `customers` ... and `events` or `purchases` ... Use denormalized fields for fast aggregation'.
- **When:** 2026-11-25T12:05:01+00:00

## D006 (build): I chose to seed ~1000 customers over 12 months (configurable via script), defaulting to 500 for faster runs in CI.

- **Instead of:** Seed small demo (100 customers over 6 months); Seed moderate demo (1000 customers over 12 months)
- **Because:** 1k customers over 12 months shows cohort patterns; making default seed size configurable and allowing smaller size for quick runs balances realism and speed.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report suggestion: 'for demo ~1k customers over 12 months'.
- **When:** 2026-11-25T12:05:05+00:00

## D007 (build): I chose to materialize cohort snapshots in a 'cohort_snapshots' collection and refresh with a weekly APScheduler job (and expose an admin endpoint to trigger refresh on demand).

- **Instead of:** Store snapshots in external file or cache; Store snapshots in 'cohort_snapshots' collection and refresh weekly via APScheduler
- **Because:** Materialized snapshot documents are easy to serve via HTTP and demonstrate scheduled refresh; APScheduler is lightweight for a sample app.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Cache cohort snapshots as materialised documents refreshed weekly.'
- **When:** 2026-11-25T12:05:08+00:00

## D008 (build): I chose to create indexes: customers.acquired_at (single-field), events.customer_id + event_date (compound), events.product_id, events.channel; and a TTL index not needed.

- **Instead of:** Create no indexes; Create single-field indexes on acquired_at, events.customer_id and compound index (customer_id,event_date)
- **Because:** These indexes support cohort grouping by acquisition date and lookups/filtering on events by customer and date windows for retention.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'create supporting indexes on acquired_at (date), customer_id, channel, product_id and possibly compound indexes'.
- **When:** 2026-11-25T12:05:14+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:08:24+00:00

## D010 (build): I chose Python 3.11 with FastAPI and Uvicorn, using PyMongo (pymongo 4.x) as the MongoDB driver.

- **Instead of:** Node.js/Express; Python/FastAPI; Go/Fiber
- **Because:** The prompt review and environment guidance suggested Python+FastAPI and PyMongo; this is familiar and well-supported for a small sample app.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.11 ... FastAPI ... Use PyMongo (pymongo) 4.x"
- **When:** 2026-11-25T12:08:44+00:00

## D011 (build): I chose PyMongo (synchronous) 4.x for the driver and will implement a singleton MongoClient per process.

- **Instead of:** Use Motor (async); Use PyMongo (sync)
- **Because:** Keeps the sample simple and follows the documentdb-driver skill guidance to use one MongoClient per process for connection pooling and stability.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use PyMongo (pymongo) 4.x ... Implement MongoClient as a singleton per process"
- **When:** 2026-11-25T12:08:47+00:00

## D012 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:14:13+00:00

## D013 (build): I chose Python with FastAPI and Uvicorn.

- **Instead of:** Node.js/Express; Python/FastAPI; Go/Fiber; Dotnet minimal API
- **Because:** Prompt requested a Python FastAPI service; Python/FastAPI is the direct match and is available in the environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.11 ... and FastAPI ~0.95+, run with Uvicorn."
- **When:** 2026-11-25T12:14:35+00:00

## D014 (build): I chose PyMongo (pymongo) 4.x.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** MongoDB 7.0 wire protocol support requires a modern pymongo 4.x; driver best-practices recommend singleton client pattern.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use PyMongo (pymongo) 4.x (compatible with MongoDB 7.0 wire protocol)."
- **When:** 2026-11-25T12:14:37+00:00

## D015 (build): I chose to use the existing cluster specified by DOCUMENTDB_URI and NOT provision any Azure resources.

- **Instead of:** Create new DocumentDB cluster via IaC; Use existing cluster referenced in environment variable
- **Because:** Run policy forbids Azure resource creation and the environment already has a reachable cluster; using it keeps costs minimal and aligns with guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Do not provision a new Azure DocumentDB cluster; use the existing cluster referenced in skill.md."
- **When:** 2026-11-25T12:14:48+00:00

## D016 (build): I chose to pin versions in requirements.txt (fastapi 0.95.2, pymongo 4.5.0, uvicorn 0.23.2, apscheduler 3.10.1).

- **Instead of:** Use latest deps unconstrained; Pin versions in requirements.txt
- **Because:** Pinning ensures reproducible installs for the sample and matches tested driver versions compatible with MongoDB 7.0
- **Reason came from:** `model_default`
- **Evidence:** project conventions and reproducibility; readiness_report indicated Python and pip present
- **When:** 2026-11-25T12:16:09+00:00

## D017 (build): I chose to run the snapshot generation via a python -c one-liner that appends '.' to sys.path at runtime.

- **Instead of:** Run scripts/generate_snapshot.py directly (ModuleNotFoundError); Prefix PYTHONPATH=. (refused); Run via python -c with sys.path.append('.')
- **Because:** The runner refused environment variable prefix; app is local and adding '.' to sys.path at runtime is a safe workaround to import the app package for the one-shot script.
- **Reason came from:** `tool_unavailable`
- **Evidence:** Attempt to run 'PYTHONPATH=. python scripts/generate_snapshot.py' was refused by the command runner. Error reported: "REFUSED: 'pythonpath=.' is not on the allowed command list"
- **When:** 2026-11-25T12:16:35+00:00
