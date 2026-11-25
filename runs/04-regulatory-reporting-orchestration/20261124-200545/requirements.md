# Reference requirements: Regulatory reporting orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline is written in Python and built with LangChain, with an orchestrator and three distinct agent roles: data extraction, validation and filing.
- The data-extraction agent queries more than one Azure DocumentDB collection through a MongoDB-compatible Python driver (e.g. PyMongo), filtering each query to the reporting period, and returns the extracted data to the orchestrator.
- The validation agent takes the extracted data, checks it for completeness and applies business rules, and returns the outcome of those checks.
- The filing agent formats the validated data into the required regulatory schema and returns the formatted output.
- The orchestrator runs the data-extraction, validation and filing agents in sequence, passing each agent's output to the next agent as its input.
- The orchestrator records each step's status as a workflow document in an Azure DocumentDB collection (e.g. one document per run that is updated with the step name and its status as each step completes).

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
