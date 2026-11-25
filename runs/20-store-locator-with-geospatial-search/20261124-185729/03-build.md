# 3. Build report: 20-store-locator-with-geospatial-search

**Status: completed**

A small Node.js + Express + Mongoose store-locator sample was created. It models stores with GeoJSON Point locations, includes a 2dsphere index on the location field, provides a /nearby endpoint that runs a $geoNear aggregation, and includes a seed script. I verified seeding, index creation (via Mongoose), and the geo query against the live Azure DocumentDB cluster. One MCP index-creation tool call failed and I fell back to the seed script to create the index.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster's connection string (do NOT commit secrets).
2) npm install
3) npm run seed    # upserts the sample stores and ensures the 2dsphere index
4) npm start       # starts the Express server on PORT (default 3000)
5) Call the endpoint: GET /nearby?lat=37.7749&lon=-122.4194&radiusMeters=5000

Additional one-shot verification (included): npm run verify will run a script that connects and runs the same $geoNear aggregation and prints results.

## Verified by running

- npm install: success (dependencies installed, exit code 0)
- npm run seed: success (Connected for seeding; upserted 5 stores; Indexes ensured; Seed finished)
- npm run verify: success (Connected for verify script; $geoNear returned 5 stores sorted by distance with distanceMeters field)
- documentdb_list_indexes (MCP): returned indexes and confirmed presence of location_2dsphere index

## Not verified

- documentdb_create_index MCP tool: failed (two attempts returned 'Error: Function failed.') so I could not create the index using the MCP create_index tool; I created the index using the sample seed script (Store.createIndexes()) instead. Evidence: documentdb_create_index tool errors during the run (logged).
- I did not start the long-running Express server inside the build run (npm start) as the run harness avoids long-running background processes; the sample includes npm start so users can run it locally.

## Open issues

None.

## Files

- `src/index.js`
- `src/models/store.js`
- `src/routes/nearby.js`
- `seed/seed.js`
- `scripts/verify_nearby.js`
- `README.md`
- `.gitignore`

