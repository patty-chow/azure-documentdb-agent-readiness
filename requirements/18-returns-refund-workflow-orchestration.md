# Reference requirements: Returns & refund workflow orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Provide a Node.js entry point that accepts a return request and starts the orchestration flow for it (e.g. an exported function or HTTP handler that takes a return request identifying the order).
- Fetch the order document for the return request from Azure DocumentDB via Mongoose and pass the fetched order document object into the orchestration.
- Implement the orchestration flow with LangChain in Node.js so that it runs three agents in sequence, a policy agent, then a refund-calculation agent, then a comms agent, with each step receiving the output of the one before it.
- Implement the policy agent as a LangChain agent that receives the order document and determines whether the return is eligible.
- Implement the refund-calculation agent as a LangChain agent that receives the order document and the policy agent's eligibility result and calculates the refund amount.
- Implement the comms agent as a LangChain agent that receives the order document, the eligibility result and the refund amount and generates the customer notification text.
- Write the final return document, holding the outcome of the flow (e.g. eligibility result, refund amount and notification), back to Azure DocumentDB via Mongoose.

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
