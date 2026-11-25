# Reference requirements: Insider threat detection pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python: repository contains Python modules/scripts that perform aggregation, embedding, storage, comparison, and nightly orchestration of the insider‑threat pipeline.
- Connect to Azure DocumentDB to read raw employee activity logs: code contains a DocumentDB query that fetches logs by employee and time window (historical and recent) and can be exercised by a reviewer.
- Aggregate raw activity logs into numerical behavioural feature vectors per employee and time window: code implements and documents the feature construction (e.g., counts, durations, event-type frequencies) and produces fixed-dimension vectors for embedding.
- Call OpenAI to obtain embeddings for the behavioural feature vectors: code makes OpenAI embeddings API calls (with inputs from the feature vectors) and uses the returned embedding arrays in subsequent steps.
- Create and persist embedding documents into Azure DocumentDB using a collection configured with a DocumentDB vector-ivf index: code inserts/upserts documents that include the embedding vector field and demonstrates the collection/index being used for vector storage.
- Compute and persist a historical centroid per employee in Azure DocumentDB: code computes the mean of an employee’s historical embeddings, stores that centroid document keyed by employee id and history window, and updates it as history grows.
- Store known anomaly profile embeddings in Azure DocumentDB: repository includes code or seed data that stores one or more anomaly profile embedding documents in the database for later comparison.
- Implement a nightly scheduled job that, for each employee, builds a recent activity embedding, then compares that embedding to the employee’s historical centroid and to the stored anomaly profile embeddings using a distance/similarity metric (e.g., cosine or Euclidean) implemented in the code.
- Flag and persist alerts when deviations exceed configurable thresholds: on significant deviation, code writes an alert record into Azure DocumentDB including employee id, timestamp, similarity/distance scores, which profile(s) matched, and the threshold values used.
- Expose comparison parameters as configurable settings (distance metric and threshold values) so a reviewer can change thresholds and reproduce different flagging outcomes.

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
