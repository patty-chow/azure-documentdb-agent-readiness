# Reference requirements: Insider threat detection pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python pipeline reads employee activity logs from Azure DocumentDB and aggregates them into one behavioural feature vector per employee (e.g. counts of actions by type over a time window) using an Azure DocumentDB aggregation pipeline.
- Each behavioural feature vector is embedded by calling OpenAI, and the returned embedding is stored on a document in Azure DocumentDB.
- A cosmosSearch index of kind vector-ivf is created in code on the embedding field, with dimensions matching the OpenAI embedding model's output and a similarity of COS, L2 or IP.
- Known anomaly profiles are held as documents in Azure DocumentDB that carry an embedding, so the pipeline can compare employee embeddings against them.
- A nightly job runs on a schedule (e.g. a cron entry or a scheduler loop) and processes every employee on each run.
- For each employee, the job computes a historical centroid from that employee's stored past embeddings and compares the employee's recent activity embedding against that centroid.
- The job compares each employee's recent activity embedding against the known anomaly profiles with a $search / cosmosSearch query against the vector-ivf index.
- Employees whose recent embedding deviates significantly (e.g. beyond a chosen distance from their centroid, or within a chosen similarity of an anomaly profile) are flagged by the job (e.g. written as alert records or reported in the run output).

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
