# Reference requirements: Inventory reorder multi-agent system

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Python using a LangChain multi-agent architecture with three agents named exactly "forecast agent", "supplier agent", and "orchestrator agent".
- The "forecast agent" must read sales velocity DocumentDB documents from Azure DocumentDB and produce numeric reorder quantities per product (i.e., fetch historical sales velocity records and return a predicted reorder quantity for each product).
- The "supplier agent" must read supplier lead time DocumentDB documents from Azure DocumentDB and select a best supplier per product based on lead time (selection logic must be coded and return at least supplier_id and lead_time).
- Launch the "forecast agent" and "supplier agent" to run in parallel (concurrently) and ensure the "orchestrator agent" waits for and consumes both agents' results.
- The "orchestrator agent" must deterministically reconcile the agents' outputs per product (use the forecast agent's quantity together with the supplier agent's selected supplier) and produce a single purchase order decision per product.
- Before creating a purchase order, the "orchestrator agent" must consult and update a shared agent memory (LangChain agent memory shared across agents) to detect and prevent duplicate orders for the same product when agents run concurrently.
- When writing a purchase order, the "orchestrator agent" must persist a purchase order DocumentDB document into Azure DocumentDB that includes, at minimum, product identifier, quantity, and supplier identifier returned by the agents.
- The system must avoid writing duplicate purchase order documents to Azure DocumentDB for the same product when a pending or recently-created order exists in shared agent memory (i.e., orchestrator skips writing and returns existing order info).
- Provide an end-to-end demonstration or test run that seeds Azure DocumentDB with sample sales velocity and supplier lead time documents, executes the LangChain multi-agent flow, and verifies that exactly one purchase order DocumentDB document is created per product as reconciled by the orchestrator.

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
