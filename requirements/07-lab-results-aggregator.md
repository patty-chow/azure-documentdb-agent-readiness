# Reference requirements: Lab results aggregator

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python using async code and Beanie ODM (the repository must contain async entry points / coroutines that initialize and use Beanie).
- Define a Beanie Document model for lab results that stores patientId, testCode, value, and timestamp fields (types and names must match exactly).
- Connect to Azure DocumentDB and persist each lab result document into a collection so that lab measurements are stored as time-series documents (one document per measurement).
- Create indexes and a storage pattern appropriate for time-series queries (e.g., compound index on patientId and timestamp or an explicit time-series document pattern) and show that queries sort/scan by timestamp efficiently.
- Implement aggregation pipelines (using MongoDB aggregation stages executed against Azure DocumentDB, not purely in Python) that compute moving averages of value over a sliding window for a given patientId and testCode.
- Make the moving-average aggregation window configurable (by number of samples or by a time range parameter) and show the pipeline accepts that parameter.
- Ensure aggregation pipelines also flag or annotate results that fall outside reference ranges (the pipeline must produce an output field such as flagged or outOfRange for those documents).
- Provide a source of reference ranges for tests (e.g., a collection or input parameter keyed by testCode) and have the aggregation pipeline consult those ranges when flagging out-of-range results.
- Open an async change stream on the lab results collection using Azure DocumentDB change streams and listen for inserts/updates to detect newly written critical values.
- When the change stream detects a critical value (defined by configurable critical thresholds), the async listener must trigger a real-time alert action (for example, call an async callback, emit a log message marked as an alert, or enqueue a notification); include a demo script that inserts a critical lab result and demonstrates the alert firing.

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
