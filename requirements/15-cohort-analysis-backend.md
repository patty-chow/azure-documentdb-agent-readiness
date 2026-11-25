# Reference requirements: Cohort analysis backend

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service as a Python FastAPI application that exposes at least one HTTP endpoint (e.g., /cohorts) returning cohort analysis JSON.
- Connect to Azure DocumentDB using the DocumentDB Atlas-compat API from Python (for example, configuring pymongo to the Azure DocumentDB Atlas-compat endpoint) and perform all reads/writes against Azure DocumentDB.
- Build and execute DocumentDB aggregation pipelines (via the driver’s aggregate API) to produce cohort data; the pipeline code must be visible in the repository.
- Use a $bucket stage in the aggregation pipeline to group customers by acquisition month (cohort key = acquisition month).
- Compute cohort retention rates at 30, 60, and 90 days from the aggregation results and include those numeric retention rates in the API response for each cohort.
- Use a $facet stage in the aggregation pipeline to produce simultaneous breakdowns by channel and by product; include both facet results in the returned cohort snapshot.
- Materialise/cache cohort snapshots as documents stored in Azure DocumentDB (a dedicated collection), including cohort month key and snapshot timestamp fields.
- Implement a scheduled weekly refresh job that runs the aggregation pipelines and upserts the materialised cohort snapshot documents in Azure DocumentDB (the scheduler code must be part of the service).
- Serve cohort API requests from the cached materialised documents in Azure DocumentDB rather than recomputing the aggregation on every request; the endpoint should read the snapshot documents and return them.

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
