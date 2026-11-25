# Reference requirements: Store locator with geospatial search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Node.js using the Mongoose ODM (i.e., Mongoose models and queries are used for all DB operations).
- Define a Store Mongoose schema where the location is stored as a GeoJSON Point document (an object with "type": "Point" and a "coordinates" array) and ensure coordinates are stored in GeoJSON order [longitude, latitude].
- Create a 2dsphere index on the location field in the Mongoose schema (schema-level index or index option) so Azure DocumentDB can serve geospatial queries.
- Include opening hours and stock availability fields on the Store schema and persist them with each store document; those fields must be returned by queries.
- Expose an HTTP endpoint at /nearby that accepts latitude, longitude, and radius (as query parameters or JSON body), parses them as numbers, and returns a 400 error for missing or invalid values.
- Construct and execute a $geoNear aggregation stage in the query pipeline, supplying the provided coordinates as the near GeoJSON Point and applying the provided radius via maxDistance (so the aggregation is actually limited to the radius).
- Specify a distanceField in the $geoNear aggregation and return that distance with each store result; ensure the aggregation output is sorted by that distance.
- Ensure the $geoNear aggregation is used (i.e., the pipeline contains a $geoNear stage) rather than only using other operators like $nearSphere or manual filtering.
- Connect Mongoose to an Azure DocumentDB (MongoDB‑compatible) endpoint for data storage; the connection URI must be configurable (e.g., via an environment variable) and used by the service at runtime.
- Return a JSON response from /nearby containing an array of stores sorted by distance where each item includes the computed distance, opening hours, and stock availability fields from the stored documents.

## What a gallery sample also needs (the starter prompt does not say these)

- The connection string and model credentials come from environment variables; none appear in the repository.
- A `.env.example` lists every setting with placeholder values.
- The vector index dimensions match the embedding model's output.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one.
- One database client is created and reused across requests.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data.
- `/search` returns a clear error for an empty query and when the embedding call fails.
- Search results include the similarity score.
- Dependencies are pinned in `requirements.txt`.
- Unit tests run without a live cluster.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name.
