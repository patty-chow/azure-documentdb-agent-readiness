# Reference requirements: Population health dashboard backend

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the backend as a Python FastAPI service that exposes HTTP endpoints for cohort-level metrics and faceted breakdowns.
- Connect to Azure DocumentDB via the DocumentDB Atlas-compat API using the PyMongo driver (MongoClient) and load connection settings from configuration.
- Implement aggregation pipelines that compute cohort-level metrics (counts, rates, aggregates) using collection.aggregate.
- Implement faceted queries that break down patient cohorts by diagnosis, age band, gender, and region using the $facet stage in a single aggregation pipeline.
- Expose an HTTP endpoint that accepts cohort filter parameters (e.g., cohort id or filter criteria) and returns the faceted aggregation result produced by the aggregation pipeline.
- Cache expensive aggregation results as materialised summary documents stored in Azure DocumentDB in a dedicated summaries collection; each summary document must include the cohort filter metadata, computed metrics, and a lastRefreshed timestamp.
- Provide a configurable scheduled refresher (e.g., APScheduler or a FastAPI background task) that re-runs the aggregation pipelines on the configured schedule and upserts the materialised summary documents into Azure DocumentDB.
- Endpoints must read and return a materialised summary document when a fresh summary exists (determined from lastRefreshed vs. the configured schedule); if no fresh summary exists the endpoint must run the aggregation pipeline and persist the new materialised summary.
- Ensure aggregation pipelines are written to scale to millions of patient records by applying $match stages early, performing grouping/counting inside the pipeline, and consuming results via aggregation cursors/batched fetching (PyMongo cursor) rather than loading all results into memory.

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
