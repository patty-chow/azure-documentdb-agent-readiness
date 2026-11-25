# Reference requirements: 360 data platform (CDP) orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline is written in Python with LangChain, and an orchestrator role runs each batch through the ingest agent, then the dedup agent, then the enrich agent, in that order.
- The ingest agent, dedup agent and enrich agent are each a distinct LangChain-based component (e.g. a LangChain agent, chain or runnable) that the orchestrator invokes.
- The ingest agent normalises incoming customer records (e.g. consistent casing, trimmed whitespace, a common field layout) and writes the normalised records to Azure DocumentDB through a MongoDB driver (e.g. PyMongo).
- The dedup agent identifies duplicate customer profiles using LLM-assisted matching: candidate profiles are passed to an LLM through LangChain, and its decision determines whether they are treated as duplicates.
- The dedup agent merges the profiles judged to be duplicates into a single profile in Azure DocumentDB.
- The enrich agent appends third-party firmographic or demographic signals (e.g. company size or industry, age range) to the customer profiles stored in Azure DocumentDB.
- The orchestrator logs each batch run as a workflow document in Azure DocumentDB (e.g. holding a run identifier, start and end times, and the stages that ran).

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
