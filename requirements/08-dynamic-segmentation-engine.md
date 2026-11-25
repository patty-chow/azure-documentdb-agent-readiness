# Reference requirements: Dynamic segmentation engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the application in Python and use LangChain as the agent framework in a single-agent configuration (i.e., one LangChain Agent instance orchestrating tools).
- Provide a LangChain-accessible tool named "DocumentDB aggregation tool" that executes aggregation pipelines against event data stored in Azure DocumentDB.
- The "DocumentDB aggregation tool" must run server-side aggregation pipelines (aggregation pipelines) against an events collection in Azure DocumentDB (not only client-side aggregation) and return the aggregation results to the agent.
- The aggregation pipelines must compute, per customer id on demand, the behavioural metrics recency (time since last event), frequency (event count per configurable lookback window), and category affinity (per-category proportions or top category scores).
- Expose an on-demand invocation path (function, CLI command, or HTTP endpoint) that accepts a customer id, triggers the agent to run the aggregation pipelines for that customer, and returns the computed metrics.
- Use context engineering to inject segmentation rules at runtime into the agent prompt (e.g., load rules from a config file or database and insert them into the system/user prompt before LLM calls); the injected rules must be visible in the code path that constructs the prompt.
- The agent must apply those injected segmentation rules (via the LLM prompt) to the computed metrics and choose a single segment label for the customer; the LLM response and chosen label must be captured by the application.
- After the agent assigns a segment label, the application must write that segment label back into the customer's profile document in Azure DocumentDB (update the profile document with the label and a timestamp) using an update operation against the profile collection.
- The code must log or return the aggregation pipeline outputs and the metric values used for segmentation so a reviewer can verify the agent's decision (e.g., structured JSON containing recency, frequency, category affinity, applied rules, chosen label).
- Include at least one end-to-end demonstration or automated integration test in the repository that inserts sample event data into Azure DocumentDB, invokes the agent for a sample customer id, and verifies that the customer's profile document in Azure DocumentDB is updated with the expected segment label and timestamp.

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
