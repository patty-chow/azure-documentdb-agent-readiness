# Reference requirements: Dynamic pricing engine

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Python LangChain agent that, given a product to price, calls LangChain tools to gather current demand metrics, competitor prices and margin rules, then recommends a new price.
- A LangChain tool that computes the product's current demand metrics in Azure DocumentDB with an aggregation pipeline (e.g. recent sales counts or sales velocity), using a MongoDB driver (e.g. PyMongo).
- A LangChain tool that queries Azure DocumentDB for the competitor price documents for the product.
- A LangChain tool that reads the margin rule documents stored in Azure DocumentDB and returns the margin constraints that apply to the product.
- The agent's prompt instructs the LLM to reason step-by-step over the demand metrics, competitor prices and margin rules before it recommends a new price.
- The recommended price is written back to the product document in Azure DocumentDB with a single atomic update of that document (e.g. update_one or find_one_and_update).

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
