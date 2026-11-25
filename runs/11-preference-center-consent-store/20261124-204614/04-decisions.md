# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| readiness_report | 4 |
| model_default | 3 |
| operator | 2 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:44:43+00:00

## D002 (build): I chose Python + FastAPI with Beanie (Motor) as the framework and ODM for the sample.

- **Instead of:** Node.js/Express+Mongoose; Python+FastAPI+Beanie; Go+Fiber+mongo-driver
- **Because:** The prompt explicitly requests Python FastAPI + Beanie, so this matches the user's requirement.
- **Reason came from:** `prompt`
- **Evidence:** User prompt: 'build a Python FastAPI service using Beanie ODM'
- **When:** 2026-11-25T11:45:06+00:00

## D003 (build): I chose Motor+Beanie singleton client.

- **Instead of:** Motor+Beanie singleton; synchronous PyMongo
- **Because:** Matches FastAPI async pattern and skill guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: Implement Motor + Beanie with a singleton Motor client
- **When:** 2026-11-25T11:45:25+00:00

## D004 (build): I chose a 365-day retention period and will populate retention_expires_at = now + 365 days on writes.

- **Instead of:** 90 days; 180 days; 365 days; no TTL
- **Because:** One year is a commonly-used retention window for consent records and is sensible for a sample; will document it in README and make it configurable via env var.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Add TTL index on expireAt/retention_expires_at with expireAfterSeconds=0' and information_gaps asked to choose a sensible default
- **When:** 2026-11-25T11:45:27+00:00

## D005 (build): I chose to pin dependencies to specific, recent compatible versions in requirements.txt.

- **Instead of:** latest unconstrained; pinned versions
- **Because:** Pinned versions improve reproducibility for the sample; I'll pick recent stable releases compatible with Beanie and FastAPI and record this decision.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report 'information_gaps' asked which exact package versions to pin; no authoritative list present.
- **When:** 2026-11-25T11:45:30+00:00

## D006 (build): I chose /consents/record (POST), /consents/withdraw (POST) and GET /consents/{customer_id} for retrieval.

- **Instead of:** /consents/record & /consents/withdraw; /consents (POST with action); /v1/consents/* endpoints
- **Because:** Clear intent-specific routes are easier to discover in a sample and match the prompt's examples.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: suggested endpoints POST /consents/record, POST /consents/withdraw, GET /consents/{customerId}
- **When:** 2026-11-25T11:45:32+00:00

## D007 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:47:13+00:00

## D008 (build): I chose Python 3 + FastAPI with Beanie (Motor) for the sample app.

- **Instead of:** Node.js/Express + Mongoose; Python + FastAPI + Beanie (Motor); Go + Gin + mongo-driver
- **Because:** FastAPI + Beanie is idiomatic for async Python apps using MongoDB-style DocumentDB and aligns with prompt guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Target Python 3.11 (current stable dev runtime) with FastAPI (ASGI) and uvicorn for dev server.'
- **When:** 2026-11-25T11:47:29+00:00

## D009 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use system env var DOCUMENTDB_URI hard-coded into config file; Read connection string from environment variable DOCUMENTDB_URI at runtime
- **Because:** Security requirement and run-environment instruction; ensures no secrets are committed.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into a file.'
- **When:** 2026-11-25T11:47:31+00:00

## D010 (build): I chose not to provision any Azure resources and to use the existing DocumentDB cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision resources (Bicep/Terraform/az); Do not provision; use existing cluster
- **Because:** Run policy forbids Azure resource changes and the environment already has a reachable cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment and run_policy: 'Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use.'
- **When:** 2026-11-25T11:47:34+00:00

## D011 (build): I chose to pin dependency versions in requirements.txt to explicit versions.

- **Instead of:** Use unpinned dependency versions; Pin dependency versions in requirements.txt
- **Because:** Ensure reproducible installs for the sample; pin to recent stable versions likely compatible with Beanie and Python 3.13.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Pin versions in requirements.txt to the tested releases.'
- **When:** 2026-11-25T11:47:37+00:00

## D012 (build): I chose to create a TTL index on field retention_expires_at with expireAfterSeconds=0 (expireAt semantics).

- **Instead of:** No TTL index created; Create TTL index on retention_expires_at with expireAfterSeconds=0
- **Because:** Matches DocumentDB indexing guidance and implements retention via expireAt.
- **Reason came from:** `readiness_report`
- **Evidence:** Guidance in readiness_report: 'Create a TTL index on a datetime field (expireAt / retention_expires_at) with expireAfterSeconds=0 and populate it with now + retention_period on writes.'
- **When:** 2026-11-25T11:47:40+00:00

## D013 (build): I chose a default retention period of 365 days for consent records in this sample.

- **Instead of:** Retention 365 days (1 year); Retention 30 days; Retention 7 years
- **Because:** One year is a sensible demo default for consent retention and easy to understand; documentable and configurable via environment variable.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report 'information_gaps' notes retention unspecified; a reasonable default needed for sample.
- **When:** 2026-11-25T11:47:42+00:00

## D014 (build): I chose to use customerId as the logical unique key and not configure sharding for the sample (single-shard).

- **Instead of:** Use customerId as unique key and not shard; Design a sharded collection with a shard key
- **Because:** Simpler for a sample app; sharding is out of scope and cluster is pre-provisioned; focus on consent model and TTL/indexing.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use customerId as the logical unique key; no sharding for sample (single-shard).'
- **When:** 2026-11-25T11:47:45+00:00

## D015 (build): I chose to implement three endpoints: POST /consents/record, POST /consents/withdraw, GET /consents/{customerId}.

- **Instead of:** Expose many endpoints including list, patch, delete; Expose minimal endpoints: record, withdraw, retrieve current state
- **Because:** Meets prompt requirements and keeps sample focused and minimal.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Expose HTTP endpoints: POST /consents/record, POST /consents/withdraw (JSON body...), GET /consents/{customerId}.'
- **When:** 2026-11-25T11:47:48+00:00

## D016 (build): I chose to update the seed script to use pymongo (synchronous) so seeding won't import Motor and avoids the motor/pymongo internal mismatch during seed execution.

- **Instead of:** Fix motor/pymongo version mismatch by changing pinned versions; Use synchronous pymongo in seed script to avoid motor import at seed time
- **Because:** Quicker and lower-risk fix for the seed script; the app runtime still uses Motor/Beanie as intended, and seed tasks do not require async driver.
- **Reason came from:** `tool_result`
- **Evidence:** Run failure: ImportError from motor referencing pymongo internals when running the seed script.
- **When:** 2026-11-25T11:48:38+00:00
