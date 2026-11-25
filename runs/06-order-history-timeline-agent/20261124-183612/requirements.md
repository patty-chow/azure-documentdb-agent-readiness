# Reference requirements: Order history & timeline agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Uses Python and LangChain: the project contains a Python implementation that constructs a Single-agent LangChain agent instance (agent framework = LangChain).
- Connects to Azure DocumentDB using the PyMongo MongoDB driver (pymongo): connection string/config is read from an environment variable and a MongoClient is created that targets the Azure DocumentDB endpoint and selects a database and an orders collection.
- Implements LangChain tools for the three required actions and registers them with the agent: fetch_order_history(customer identifier), run_spend_aggregation(customer identifier + optional time-range), and lookup_order_status(order_id).
- The spend-summary tool executes real MongoDB aggregation pipelines via PyMongo aggregate (explicitly using MongoDB aggregation) to produce spend summaries (e.g., total_spent, order_count) and supports at least a "last month" pipeline and arbitrary date-range inputs.
- The fetch_order_history tool queries Azure DocumentDB (orders collection) with a MongoDB find() that returns recent orders for a customer (includes fields such as order_id, order_date, items, total_amount, status) and paginates or limits results in code.
- The lookup_order_status tool queries Azure DocumentDB for a single order_id and returns status plus key metadata (order_date, total_amount, brief items list); if the order_id is not found it returns a clear "order not found" indication.
- Uses LangChain agent memory (agent memory) to persist conversation context across turns and explicitly stores at minimum the last-referenced customer identifier and the last-referenced time-range so follow-up questions can be resolved.
- The LangChain agent is wired so it invokes the registered tools programmatically (e.g., via AgentExecutor/Tool API) and composes tool outputs into human-readable replies rather than returning raw tool data.
- Includes an executable example or unit test that demonstrates conversational context resolution: e.g., ask the agent "show order history for customer X" then send "what about last month?" and the agent uses agent memory to resolve the customer and returns the last-month aggregation or filtered history.
- All database operations in code explicitly run against Azure DocumentDB (resource = Azure DocumentDB) and use MongoDB-compatible query/aggregation operators; the repository includes at least one documented example aggregation pipeline and one documented find() query against the orders collection.
- Handles empty or error cases gracefully: when no orders match a query or aggregation returns no data the agent responds with an informative message (e.g., "no orders found for that customer/time range") and database errors are caught and surfaced as friendly messages.

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
