# Reference requirements: Regulatory reporting orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the orchestrator in Python using a Python LangChain orchestration pipeline that sequences and coordinates the agents.
- Include a data-extraction agent named "data-extraction agent" that queries multiple DocumentDB collections for a provided reporting period parameter and returns the combined dataset.
- In the data-extraction agent, connect to Azure DocumentDB and execute filtered queries against at least two distinct DocumentDB collections (show the query strings and the reporting-period date filter in code).
- The orchestrator must invoke agents in order: data-extraction agent -> validation agent -> filing agent, and only proceed to the next agent when the previous agent reports success.
- Implement a validation agent named "validation agent" that programmatically checks completeness (e.g., required fields present) and applies business rules (at least one rule implemented, e.g., totals reconciliation or cross-collection referential integrity), returning a validation summary with pass/fail counts and detailed failure records.
- If the validation agent reports failures, the orchestrator must record the failure and halt the filing step; the workflow document must include the validation failure details.
- Implement a filing agent named "filing agent" that transforms the validated data into the required regulatory schema (produce a final payload that matches the target schema in code) and returns the formatted output.
- The filing agent must persist the formatted regulatory output (the final payload) into Azure DocumentDB (store into a DocumentDB collection or return it alongside a persisted record).
- The orchestrator must log each step's status as a workflow document in DocumentDB: for each agent run include agent name, step start and end timestamps, status (success/failure), error messages if any, and pointers to the input and output documents/collections.
- Provide code examples or test scripts that demonstrate the full run: supplying a reporting period parameter, executing data extraction across multiple DocumentDB collections, running validation rules, producing the regulatory-formatted output, and verifying that a workflow document was created in DocumentDB reflecting each step's status.

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
