# Reference requirements: Transaction categorization agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample as a Node.js application that constructs and runs a LangChain agent to perform the categorization workflow.
- Connect to Azure DocumentDB and read only uncategorised transaction documents (e.g., where "category" is missing, null, or empty) before sending them to the agent.
- When invoking the LLM from the LangChain agent, include the transaction merchant name and amount in the prompt for each transaction and use explicit prompt engineering (for example: fixed taxonomy, few-shot examples, and an instruction to return a single category label) to instruct the model to choose one category from a fixed, in-code taxonomy.
- Define the fixed taxonomy (a concrete list of category strings) in the application code and refuse or map any LLM responses that are not one of those taxonomy values.
- Have the LangChain agent write the chosen category back to the same Azure DocumentDB document (update the document’s "category" field) and mark only the processed transaction as updated.
- Use Azure DocumentDB’s aggregation capability (MongoDB aggregation pipeline) to compute monthly spend totals grouped by category (e.g., group by year-month derived from the transaction date and by category, summing the amount field).
- Expose an HTTP aggregation endpoint in the Node.js app (GET /monthly-spend or similar) that runs the DocumentDB aggregation and returns JSON showing per-month, per-category spend breakdown.
- Ensure the aggregation output uses calendar months (year-month) as the time key and includes category, total amount, and month in the JSON response so a reviewer can verify the grouping and sums.
- Ensure the agent’s categorization step only relies on merchant name and amount (and, if present, date) as input features and the code demonstrates those fields being passed into the LangChain prompt.

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
