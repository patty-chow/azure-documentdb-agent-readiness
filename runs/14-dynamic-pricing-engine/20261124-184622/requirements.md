# Reference requirements: Dynamic pricing engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the project in Python and expose a single-agent built with LangChain.
- Provide three LangChain Tools that query Azure DocumentDB: one that returns current demand metrics, one that returns competitor price documents, and one that returns margin rule documents; each tool must return structured data consumable by the agent.
- The demand-metrics tool must compute demand signals by executing an Aggregation pipelines query in Azure DocumentDB (aggregation pipeline must be visible in the code).
- The competitor-prices tool must query competitor price documents and return the most recent prices (timestamped) for the requested product SKU or product id.
- The margin-rules tool must fetch margin rule documents from Azure DocumentDB and expose rule fields (e.g., cost, min_margin, max_margin) so the agent can enforce them.
- Implement a LangChain Tool (or use the agent) that performs the update back to the product document in Azure DocumentDB using a single atomic update operation (a single find-and-modify / find_one_and_update or equivalent atomic update) that sets the new price and an updated_at timestamp and returns the updated product document.
- Use prompt engineering: include a prompt template given to the LLM that explicitly instructs it to "reason step-by-step" (show intermediate reasoning) and then produce a final recommended_price; the template must require a machine-readable final output (e.g., JSON with recommended_price) that the agent parses programmatically.
- The agent must call the three query Tools during its reasoning run (not bypass them) and incorporate their returned data into the step-by-step reasoning before producing the final recommended price.
- Before performing the atomic write, the agent must validate the recommended price against the retrieved margin rule documents and adjust or reject the recommendation so the stored price never violates the margin rules; this validation and any adjustment must be implemented in code and observable in the update logic.

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
