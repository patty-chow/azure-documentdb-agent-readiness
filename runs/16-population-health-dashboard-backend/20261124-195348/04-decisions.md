# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 4 |
| skill | 4 |
| prompt | 3 |
| operator | 1 |
| tool_unavailable | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:56:19+00:00

## D002 (build): I chose Python with FastAPI (modern ASGI framework) as the language and web framework for the sample.

- **Instead of:** Node.js/Express; Python/FastAPI; Go/Gin
- **Because:** The user explicitly requested "build a Python FastAPI service" in the sample prompt, so Python/FastAPI is the correct choice.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use a recent stable Python 3.x — e.g., Python 3.10 or 3.11 for the sample and CI." and the sample prompt asked for a "Python FastAPI service".
- **When:** 2026-11-25T08:56:39+00:00

## D003 (build): I chose Python 3.11 as the target minor version for the sample.

- **Instead of:** Python 3.10; Python 3.11; Python 3.13
- **Because:** 3.11 is a recent stable release with broad compatibility for examples and CI; it matches the prompt review suggestion.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Use a recent stable Python 3.x — e.g., Python 3.10 or 3.11 for the sample and CI."
- **When:** 2026-11-25T08:56:42+00:00

## D004 (build): I chose to create a singleton MongoClient (pymongo.MongoClient) and reuse it across the FastAPI app.

- **Instead of:** Create new MongoClient per request; Create a singleton MongoClient on app startup
- **Because:** Singleton MongoClient avoids connection-pool exhaustion and follows the documentdb-driver/connection best practice.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: "Connect using the SRV-style connection string from DOCUMENTDB_URI ... and create a singleton MongoClient in your FastAPI app (do not create a new client per request)." (documentdb-connection skill guidance)
- **When:** 2026-11-25T08:56:45+00:00

## D005 (build): I chose APScheduler (BackgroundScheduler) as an in-process scheduler to refresh materialized summaries on a schedule.

- **Instead of:** APScheduler in-process scheduler; External scheduler (Azure Functions/Logic Apps/Cron)
- **Because:** For a small sample app it's simplest to show scheduling inside the app process; APScheduler is a common lightweight choice that lets developers see refresh behavior without external infra.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review assumption: "Builder will use a single-agent, no-orchestration approach (one process running FastAPI with background scheduler)."
- **When:** 2026-11-25T08:56:47+00:00

## D006 (build): I chose database 'sample_healthcare_16' with collections 'patients' and 'aggregations_cache'.

- **Instead of:** Use database/sample_healthcare_16.patients and aggregations_cache; Use different collection names
- **Because:** Matches the prompt's run environment instruction and the readiness guidance to store materialised summaries in a cache collection with TTL.
- **Reason came from:** `prompt`
- **Evidence:** Readiness instructions: "Use the database named `sample_healthcare_16` for everything this sample creates." and guidance to store materialised summaries in a dedicated cache collection.
- **When:** 2026-11-25T08:56:51+00:00

## D007 (build): I chose to generate 5,000 synthetic patient records for the seed script.

- **Instead of:** Seed 500 records; Seed 5,000 records; Seed 50,000 records
- **Because:** 5,000 is in the 'few thousand' range—large enough to produce meaningful facet buckets for the sample while remaining quick to insert for testing.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Provide an idempotent seed script that generates synthetic patient data (e.g., a few thousand records)".
- **When:** 2026-11-25T08:56:54+00:00

## D008 (build): I chose to create single-field indexes on 'diagnoses' (multikey), 'gender', 'region', and 'age', plus a TTL index on 'expiresAt' in the 'aggregations_cache' collection.

- **Instead of:** Create single-field indexes on fields used by queries and a TTL index on cache; Don't create indexes (leave to user)
- **Because:** These indexes support the aggregation $match and $facet stages and the TTL ensures cached summaries can expire automatically; they follow documentdb-indexing guidance.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: "create single-field or compound indexes on the fields used by the match and facets" and "Store materialized summaries in a dedicated cache collection ... with a TTL index (expireAfterSeconds: 0)".
- **When:** 2026-11-25T08:56:57+00:00

## D009 (build): I chose a default refresh schedule of once per hour for the materialized summaries, with an endpoint to trigger immediate refreshes.

- **Instead of:** Refresh cached summaries every 15 minutes; Refresh every 1 hour; Refresh daily
- **Because:** Hourly refresh balances currency with cost and is a reasonable default for population-health dashboards; making it configurable allows users to adjust later.
- **Reason came from:** `model_default`
- **Evidence:** Prompt asked for summaries refreshed "on a schedule" but didn't specify frequency; prompt review suggested choosing a schedule.
- **When:** 2026-11-25T08:57:00+00:00

## D010 (build): I chose to install Python dependencies now using pip install -r requirements.txt to run unit tests in this environment.

- **Instead of:** Assume developer will install deps manually; Install dependencies now with pip
- **Because:** To verify unit tests we need dependencies available; installing from requirements.txt is straightforward and allowed by run policy.
- **Reason came from:** `tool_unavailable`
- **Evidence:** Tests failed because pytest was not found on PATH. The run environment description said pip is available and a virtualenv is expected.
- **When:** 2026-11-25T08:58:02+00:00

## D011 (build): I chose to run the seed script now to create the 'patients' collection, indexes, and upsert 5000 synthetic patient documents into the live cluster pointed to by DOCUMENTDB_URI.

- **Instead of:** Skip seeding (require user to run); Run the seed script now against the cluster
- **Because:** Verification requires data in the sample database; seeding 5,000 records is idempotent and quick to run and helps verify the aggregation behavior against the live cluster.
- **Reason came from:** `prompt`
- **Evidence:** Prompt run environment: "A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI." and the sample requirements to seed data.
- **When:** 2026-11-25T08:58:27+00:00

## D012 (build): I chose to run a live aggregation against the cluster (compute facets for the whole cohort) to verify the aggregation pipeline executes correctly on the seeded data.

- **Instead of:** Don't run live query; Run live aggregation against cluster to verify aggregation and index usage
- **Because:** Completes verification that the sample's aggregation pipelines work and return expected structure against real data.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Verify against the live cluster: create the collections and indexes, load the sample data, run the queries the sample exists to show, and record in the build report what was actually executed and what was not."
- **When:** 2026-11-25T09:06:18+00:00

## D013 (build): I chose to upsert the computed summary into the 'aggregations_cache' collection to verify the materialized summary write and TTL index exist.

- **Instead of:** Do not upsert summary; Upsert computed summary into aggregations_cache to verify materialized cache behavior
- **Because:** Verifies that the cache collection accepts upserts and stores summary documents as intended.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: "Store materialized summaries in a dedicated cache collection ... with a TTL index" and earlier startup code created the TTL index.
- **When:** 2026-11-25T09:06:31+00:00

## D014 (build): I chose to create the TTL index on aggregations_cache.expiresAt now via a small script to verify the cache expiration behaviour is set up.

- **Instead of:** Leave TTL index to app startup; Create TTL index now via script
- **Because:** Main startup path would create the TTL index when running the FastAPI app; creating it now ensures verification in this run that TTL index exists without having to start the full server.
- **Reason came from:** `skill`
- **Evidence:** Guidance_for_builder: "Store materialized summaries in a dedicated cache collection ... with a TTL index (expireAfterSeconds: 0)".
- **When:** 2026-11-25T09:06:48+00:00
