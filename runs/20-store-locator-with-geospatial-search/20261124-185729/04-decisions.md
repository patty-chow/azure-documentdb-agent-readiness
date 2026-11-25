# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 5 |
| prompt | 3 |
| model_default | 3 |
| operator | 2 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:21:34+00:00

## D002 (build): I chose to use Node.js with Mongoose (Mongoose 7.x) as the ODM

- **Instead of:** Use plain MongoDB Node driver (mongodb); Use Mongoose ODM (mongoose)
- **Because:** The prompt explicitly requests Mongoose; it simplifies schema, index definitions and aggregation wiring for a sample app.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js Mongoose service'
- **When:** 2026-11-25T06:21:50+00:00

## D003 (build): I chose to use Mongoose ^7.0.0 (latest 7.x) in package.json

- **Instead of:** Pin exact Mongoose version (e.g., 7.9.0); Use caret to allow latest 7.x (e.g., ^7.0.0)
- **Because:** Keeps compatibility with Node 24 and allows receiving minor fixes while staying in Mongoose 7 major version.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'recent Mongoose compatible with Node 24 (e.g., latest stable Mongoose 7.x)'
- **When:** 2026-11-25T06:21:54+00:00

## D004 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime

- **Instead of:** Read connection string from a config file; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Security and run-policy: must not write secrets to files. The environment variable is provided by the run environment and is required for connecting to the live cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Read the provided DOCUMENTDB_URI environment variable at runtime and pass it unchanged to mongoose.connect'
- **When:** 2026-11-25T06:22:00+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing provided cluster only

- **Instead of:** Provision a new DocumentDB cluster; Use the existing provided cluster and do not provision
- **Because:** Provisioning is disallowed and unnecessary; the sample should use the existing cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and readiness report notes a reachable cluster with DOCUMENTDB_URI
- **When:** 2026-11-25T06:22:04+00:00

## D006 (build): I chose to keep the stores collection unsharded for this sample

- **Instead of:** Shard the collection and pick a shard key; Keep single-shard (no sharding) for the sample
- **Because:** Sharding introduces complexity and requires cluster changes; for this sample the focus is geo queries and 2dsphere index behaviour, not scaling across shards.
- **Reason came from:** `model_default`
- **Evidence:** Sample scope: a small demo app with ~10 stores; no requirement to demonstrate sharding
- **When:** 2026-11-25T06:22:07+00:00

## D007 (build): I chose to create a 2dsphere index on the 'location' GeoJSON Point field and keep other fields unindexed by default

- **Instead of:** Use 2dsphere index on 'location' field only; Also add additional indexes for stock or opening hours
- **Because:** The primary goal is demonstrating geo search with $geoNear; adding secondary indexes isn't necessary for this sample and keeps write cost low.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create your geospatial index with a 2dsphere index on the GeoJSON Point field and use $geoNear...'
- **When:** 2026-11-25T06:22:10+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:23:59+00:00

## D009 (build): I chose Node.js + Express + Mongoose (Mongoose 7.x) for the sample.

- **Instead of:** Python/Flask with PyMongo; Node.js + Express + Mongoose; Go with mgo driver
- **Because:** The prompt requested a Node.js Mongoose service and the run environment provides Node 24 and npm; Mongoose 7.x is compatible with Node 24 and is the standard ODM for MongoDB in Node.js.
- **Reason came from:** `prompt`
- **Evidence:** <assumptions_from_prompt_review>: 'Builder will pick a recent Mongoose compatible with Node 24 (e.g., latest stable Mongoose 7.x)'.
- **When:** 2026-11-25T06:24:26+00:00

## D010 (build): I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime and not write secrets to files.

- **Instead of:** Embed secrets in files; Read DOCUMENTDB_URI from environment variables
- **Because:** Security best-practice and explicit guidance from readiness report; also avoids committing secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: 'Read the provided DOCUMENTDB_URI environment variable at runtime and pass it unchanged to mongoose.connect'
- **When:** 2026-11-25T06:24:28+00:00

## D011 (build): I chose to create a 2dsphere index on the location field using the documentdb MCP server's create_index tool for verification, and include index definition in the Mongoose model for runtime.

- **Instead of:** Create index via Mongoose model.ensureIndexes; Create index using documentdb MCP server with create_index tool
- **Because:** Using MCP create_index gives authoritative verification of index creation on the live cluster; including it in the model keeps the sample complete for users running the seed script.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create your geospatial index with a 2dsphere index on the GeoJSON Point field and use $geoNear as the first aggregation stage'
- **When:** 2026-11-25T06:24:32+00:00

## D012 (build): I chose to include a Mongoose seed script in the repo for users, but to perform verification in this build run using the documentdb MCP server tools to insert sample documents and create indexes.

- **Instead of:** Seed and verify using only Mongoose seed script; Seed and verify using documentdb MCP server tools
- **Because:** MCP server allows programmatic verification in this environment without exposing secrets in files; a seed script still helps end-users run the sample themselves.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'the documentdb MCP server is present and available with tools (create_index, aggregate, ...)'
- **When:** 2026-11-25T06:24:35+00:00

## D013 (build): I chose to accept lat, lon and radiusMeters as query parameters (e.g., /nearby?lat=...&lon=...&radiusMeters=...) and document this in the README.

- **Instead of:** Accept lat/lon/radius in JSON body; Accept lat/lon/radius as query parameters
- **Because:** Query parameters make the endpoint easy to call in browsers and curl; it's a common pattern for simple read-only queries and matches the sample's focus on demonstration rather than complex request bodies.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information_gaps: 'The prompt did not specify whether /nearby should accept lat/lon/radius as query parameters or JSON body'
- **When:** 2026-11-25T06:24:38+00:00

## D014 (build): I chose to fallback to creating the 2dsphere index via the Mongoose seed script (Store.createIndexes) because the documentdb_create_index MCP tool failed after two attempts.

- **Instead of:** Continue retrying documentdb_create_index; Fallback to creating the index via Mongoose (Store.createIndexes) and seed script
- **Because:** Mongoose createIndexes will create the index on the live cluster using the provided DOCUMENTDB_URI; the MCP tool was unavailable so this is a safe alternative for verification. The seed script already calls createIndexes.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index tool returned 'Error: Function failed.' on two attempts.
- **When:** 2026-11-25T06:25:38+00:00
