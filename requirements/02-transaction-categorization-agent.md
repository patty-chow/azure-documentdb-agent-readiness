# Reference requirements: Transaction categorization agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js LangChain agent reads transactions that have not yet been categorised from Azure DocumentDB through a MongoDB-compatible Node.js driver (e.g. the `mongodb` package), selecting documents that carry no category.
- The agent reaches Azure DocumentDB through LangChain tools (e.g. one tool that fetches uncategorised transactions and one that writes a category back), and the agent decides when to invoke them.
- The prompt is engineered to instruct the LLM to assign exactly one category from a fixed taxonomy: the taxonomy is defined in the application, listed in the prompt, and the LLM is told to choose only from it.
- The prompt includes each transaction's details (e.g. merchant name and amount) so the LLM reasons over them when choosing the category.
- The category the LLM assigns is written back to the same transaction document in Azure DocumentDB (e.g. an update that sets a category field on that document).
- An HTTP endpoint returns the monthly spend breakdown by category.
- That breakdown is computed by an aggregation pipeline run in Azure DocumentDB that groups transactions by month and by category and sums their amounts (e.g. `$group` on a month derived from the transaction date plus the category, with `$sum` of the amount).

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
