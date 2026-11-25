DocumentDB Store Locator Sample

This sample demonstrates storing GeoJSON Point locations in Azure DocumentDB and performing geospatial search with a 2dsphere index and the $geoNear aggregation stage.

What it shows
- A Node.js + Express + Mongoose service exposing GET /nearby?lat=&lon=&radiusMeters= which returns stores sorted by distance (distanceMeters) using $geoNear.
- A Mongoose model with a GeoJSON Point and a 2dsphere index on the location field.
- A seed script (seed/seed.js) that upserts a few sample stores.

Prerequisites
- Node.js 24+, npm
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in a .env file or environment to the cluster's connection string. Example in .env.example.
- The sample uses the database name sample_retail_20. It will create the stores collection and indexes if needed.

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI.
2. Install dependencies: npm install
3. Seed sample data: npm run seed
4. Start the server: npm start
5. Call the endpoint: GET http://localhost:3000/nearby?lat=37.7749&lon=-122.4194&radiusMeters=5000

Verification in this build run
- This repository includes scripts used by the build to create the 2dsphere index and insert seed documents via the documentdb MCP server for automated verification. See BUILD_REPORT.md for the actual actions taken during the build and verification results.

Security
- Do NOT commit real connection strings. Use environment variables. The app reads DOCUMENTDB_URI at runtime.

License
- Sample code provided as-is for demonstration purposes.
