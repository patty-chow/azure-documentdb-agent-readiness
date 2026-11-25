# Reference requirements: Multi-touch attribution model

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Python and have it connect to Azure DocumentDB to read and write documents.
- Read time-series customer journey event documents from Azure DocumentDB; each event document used by the sample must include at minimum: customer_id, timestamp (or event_time), touchpoint (channel identifier), and revenue (or value) fields.
- Implement three attribution computations — first-touch, last-touch, and linear — as aggregation pipelines executed against Azure DocumentDB (use the database-side MongoDB-compatible aggregation pipelines, not purely in-process aggregation).
- Each aggregation pipeline must group events by customer_id, order events by timestamp, and compute per-touchpoint revenue allocations according to the model rules (first-touch: 100% to earliest touch; last-touch: 100% to latest touch; linear: equal split across all touches).
- For each customer and pipeline run, produce an attribution result document that includes: customer_id, model name (first-touch/last-touch/linear), total_revenue, per_touchpoint allocation breakdown, event_count, and the pipeline run timestamp.
- Store attribution results as versioned documents per customer in Azure DocumentDB: each pipeline run must INSERT a new versioned document (do not overwrite prior versions) and include a version identifier (numeric or ISO timestamp) and metadata referencing the source event time range used.
- Provide an API or function in the Python service to re-run attribution pipelines for a given customer or time range that creates a new versioned attribution document rather than replacing existing versions.
- Implement a LangChain tool in Python that accepts natural-language queries from marketers, translates those queries into lookups/queries against the stored, versioned attribution documents in Azure DocumentDB, and returns answers drawn from the attribution documents.
- The LangChain tool responses must include which attribution model and which version identifier (version id or timestamp) were used to produce the answer, and support at minimum queries such as “What was the first-touch allocation for customer <id>?” and “Show the linear attribution breakdown for customer <id> (latest or specific version).”
- Include an end-to-end demonstration in code that loads a sample set of time-series event documents into Azure DocumentDB, runs the three aggregation pipelines to create versioned attribution documents, and shows the LangChain tool answering at least one natural-language question against those stored results.

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
