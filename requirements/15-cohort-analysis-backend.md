# Reference requirements: Cohort analysis backend

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python FastAPI service exposes HTTP endpoints that return cohort analysis results.
- The cohort computation is an aggregation pipeline that Azure DocumentDB executes, sent through a MongoDB driver (e.g. PyMongo).
- The pipeline uses a `$bucket` stage to group customers by acquisition month.
- The pipeline computes retention rates at 30, 60 and 90 days for each cohort.
- The pipeline uses a `$facet` stage to break the cohorts down by channel and by product.
- Cohort snapshots are cached as materialised documents stored in Azure DocumentDB (e.g. a snapshots collection), produced by running the pipeline.
- A weekly refresh re-runs the pipeline and replaces the materialised snapshot documents.
- The cohort endpoints serve their results from the cached snapshot documents.

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
