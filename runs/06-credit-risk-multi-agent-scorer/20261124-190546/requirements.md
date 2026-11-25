# Reference requirements: Credit risk multi-agent scorer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Python with LangChain as a multi-agent setup with three distinct agents, a data-fetch agent, a scoring agent and an explainer agent, coordinated by a pipeline that runs them in that order for an applicant and passes each agent's output on to the next.
- The data-fetch agent takes an applicant as input and retrieves that applicant's history from Azure DocumentDB through a Python MongoDB driver (e.g. pymongo), returning the fetched history to the pipeline.
- The scoring agent applies risk rules to the fetched history and calls an LLM through LangChain to produce a credit score.
- The explainer agent calls an LLM through LangChain to generate a human-readable rationale for the credit score from the scoring agent's result.
- After the explainer agent runs, the pipeline stores the final credit score and the explanation back in Azure DocumentDB for that applicant (e.g. as fields on the applicant's document).

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
