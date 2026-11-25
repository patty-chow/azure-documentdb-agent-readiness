# Reference requirements: Population health dashboard backend

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python FastAPI service exposes HTTP endpoints for a population health dashboard, each returning cohort-level metrics computed by an aggregation pipeline run on the patient records in Azure DocumentDB through the Python driver (e.g. PyMongo).
- The faceted-query pipeline uses a $facet stage with one sub-pipeline per breakdown dimension: diagnosis, age band, gender and region.
- Each $facet sub-pipeline groups or buckets the patient cohort into that dimension's categories and computes a per-category metric (e.g. patient count), with the age band derived in the pipeline from the patient's age or date of birth (e.g. $bucket).
- Expensive aggregation results are written by the service into Azure DocumentDB as materialised summary documents in a collection of their own (e.g. a summaries collection).
- A scheduled refresh (e.g. a background scheduler or periodic task) recomputes the expensive aggregations and replaces the materialised summary documents on a recurring schedule.
- Dashboard endpoints that serve the cached aggregations read the stored materialised summary documents from Azure DocumentDB.

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
