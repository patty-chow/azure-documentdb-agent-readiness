# Reference requirements: Lab results aggregator

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in async Python with the Beanie ODM: define a Beanie Document model for lab results and insert instances into an Azure DocumentDB collection.
- Store each lab result as its own time-series document carrying the fields patientId, testCode, value and timestamp.
- Provide an aggregation pipeline, run through Beanie, that computes a moving average of value over time-ordered results for a patient and test (e.g. $setWindowFields partitioned by patientId and testCode over a window of recent documents).
- Flag results whose value falls outside the reference range for the test inside the aggregation pipeline, marking out-of-range results in the pipeline output (e.g. a boolean field added with $addFields).
- Open a change stream on the lab results collection and consume its events asynchronously as new results are written.
- When a change event carries a critical value (e.g. beyond a critical threshold for the test), trigger a real-time alert from the change-stream handler.

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
