Hospital Bed Occupancy Sample (Azure DocumentDB - Mongoose)

This sample demonstrates:
- Using Mongoose to connect to an Azure DocumentDB (MongoDB-wire) cluster
- Opening a change stream on a collection to react to bed status changes
- Maintaining per-ward occupancy summaries atomically
- Using a TTL index to expire cleaning-state documents automatically

Prerequisites
- Node.js 24+ and npm
- An Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in your environment
  (see .env.example for format)

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI and CLEANING_TTL_SECONDS as desired.
2. Install dependencies:
   npm install
3. Seed sample data:
   npm run seed
4. Run the demo (starts a short-lived change-stream watcher and performs some updates):
   npm run demo

Optional: run the Express server to inspect ward summaries (runs indefinitely):
  npm start
  GET /wards/ward-A/summary

Notes
- Do not commit real secrets. Keep DOCUMENTDB_URI in environment or a secure store.
- The sample creates indexes (including a TTL index on cleaningExpiresAt) during seeding.
- The demo opens a short-lived change stream and updates some bed statuses to show summaries being updated.

Files
- src/: source files
- src/seed.js: idempotent seeding of wards and beds
- src/demo.js: one-shot demo that starts watcher, updates beds, and exits
- src/server.js: small Express API
- .env.example: example environment variables

Verification
The build report includes what was actually executed during the automated verification steps.
