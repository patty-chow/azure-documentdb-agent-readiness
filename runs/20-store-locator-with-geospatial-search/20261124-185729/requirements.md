# Reference requirements: Store locator with geospatial search

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Define a Mongoose model for stores in a Node.js service whose location is stored as a GeoJSON Point (type "Point" with a [longitude, latitude] coordinates array) in Azure DocumentDB.
- Create a 2dsphere index on the GeoJSON location field in code (e.g. declared on the Mongoose schema with schema.index({ location: '2dsphere' })).
- Expose a /nearby HTTP endpoint that accepts a latitude, a longitude and a radius as inputs (e.g. query parameters).
- Have the /nearby handler run a $geoNear aggregation through Mongoose against Azure DocumentDB, using the request's latitude and longitude as the near point and the request's radius as the maximum distance.
- Return the matching stores ordered by distance from the request point, nearest first (the $geoNear stage supplies the ordering).
- Include each store's opening hours and stock availability in the /nearby response, taken from the stored store document (e.g. openingHours and stock fields).

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
