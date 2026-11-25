# Reference requirements: CLV prediction pipeline

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution in Python and instantiate a Single-agent LangChain agent (imports and agent construction must show Python and LangChain).
- Register and expose a DocumentDB aggregation tool as a LangChain tool that the agent can call (tool implementation must be named or documented as the "DocumentDB aggregation tool").
- The DocumentDB aggregation tool must execute aggregation pipelines against Azure DocumentDB and use aggregation stages to compute, per customer, historical purchase frequency, average order value, and tenure (e.g., $match + $group + $avg/$sum and date min/max or equivalent aggregation operators).
- The aggregation pipeline implementation must accept a customer identifier input and return the computed metrics in machine-readable form (JSON/dict) for that customer.
- The LangChain agent must assemble a prompt template (prompt engineering) that injects the aggregated metrics and explicitly instructs the LLM to estimate a CLV tier using the categories "low, medium, high, VIP".
- The prompt template must also instruct the LLM to produce a numeric CLV score and a concise textual rationale for the score; the agent code must pass the rationale through in the LLM response.
- The agent must call the DocumentDB aggregation tool during its run and feed the returned aggregation results into the LLM prompt (demonstrable in the agent-tool invocation code).
- The agent must parse the LLM output to extract a numeric CLV score and the selected tier (exactly one of "low", "medium", "high", "VIP") and include the rationale in the parsed result.
- The application must update the customer profile document in Azure DocumentDB by writing the CLV score and CLV tier back to that document using an update operation filtered by the same customer identifier (code must show the update query).
- Include a runnable end-to-end example (script or main function) that, for a sample customer ID, runs the aggregation tool, invokes the LangChain agent prompt flow, logs the rationale and outputs, and persists the CLV score and tier to Azure DocumentDB.

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
