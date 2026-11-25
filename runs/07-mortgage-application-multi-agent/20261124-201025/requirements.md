# Reference requirements: Mortgage application multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The pipeline is written in Node.js and built with LangChain: an orchestrator coordinates three LangChain agents, one each for underwriting, compliance and customer communications.
- The orchestrator reads a mortgage application document from Azure DocumentDB with the MongoDB Node.js driver (e.g. `mongodb`) and hands it to the underwriting agent.
- The underwriting agent assesses the applicant's affordability from the application document and returns its assessment to the orchestrator.
- The compliance agent receives the application together with the underwriting assessment, checks regulatory requirements, and returns its result to the orchestrator.
- The comms agent receives the application plus the underwriting and compliance results and drafts the decision letter.
- The orchestrator runs the agents in sequence, underwriting then compliance then comms, with each agent receiving the previous agent's output.
- After the comms agent finishes, the orchestrator writes the outcome (e.g. the affordability assessment, compliance result and decision letter) back to Azure DocumentDB.

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
