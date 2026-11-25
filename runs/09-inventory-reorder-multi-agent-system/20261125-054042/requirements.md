# Reference requirements: Inventory reorder multi-agent system

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python LangChain multi-agent system with three agent roles: a forecast agent, a supplier agent and an orchestrator agent.
- The forecast agent reads sales velocity documents from Azure DocumentDB with the Python MongoDB driver (e.g. PyMongo) and predicts a reorder quantity from them.
- The supplier agent reads lead time documents from Azure DocumentDB and selects the best supplier based on lead time (e.g. the shortest).
- The orchestrator agent coordinates the forecast agent and the supplier agent and reconciles their results into a reorder decision.
- The orchestrator writes purchase order documents to Azure DocumentDB for the reorders it decides on.
- Shared agent memory is used by the orchestrator to detect an order already placed for the same item and skip it, and a newly written purchase order is recorded in that memory.

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
