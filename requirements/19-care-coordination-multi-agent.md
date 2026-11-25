# Reference requirements: Care coordination multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The system is written in Python with LangChain and has four distinct agent roles: an orchestrator and three worker agents (GP, specialist, pharmacy), each a separate LangChain agent or runnable with its own instructions and tools.
- The GP agent reads the patient's primary care record from Azure DocumentDB using a MongoDB-compatible Python driver (e.g. PyMongo) and returns it to the orchestrator.
- The specialist agent retrieves the patient's referral notes from Azure DocumentDB and returns them to the orchestrator.
- The pharmacy agent reads the patient's current medications from Azure DocumentDB and returns them to the orchestrator.
- The orchestrator invokes all three worker agents for a given patient and collects their results.
- The orchestrator synthesises a single unified care plan document from the three agents' results through a LangChain LLM call.
- The orchestrator writes the unified care plan document back to Azure DocumentDB (e.g. an insert into a care-plans collection).

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
