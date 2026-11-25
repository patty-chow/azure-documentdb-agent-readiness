# Reference requirements: Credit risk multi-agent scorer

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Python and build the pipeline using LangChain as a multi-agent system, explicitly defining three agents named "data-fetch agent", "scoring agent", and "explainer agent".
- The data-fetch agent must connect to Azure DocumentDB (MongoDB-compatible) using a configurable connection string (not hard-coded) and query an applicant collection by applicant ID to return the applicant's persisted history (credit history/transactions, income, debts, past loans).
- The data-fetch agent must return a structured Python dict/JSON containing the retrieved fields so the pipeline can pass them to downstream agents.
- The scoring agent must include deterministic, inspectable risk-rule code (at least two explicit rules, e.g., debt-to-income threshold and missed-payments threshold) that computes a rule-based score and exposes the rule evaluations in its output.
- The scoring agent must also invoke an LLM via LangChain (e.g., an LLMChain or equivalent LangChain call) to produce or refine a final credit score, and include both the rule-based score and the LLM-derived final score in its output.
- The explainer agent must consume the applicant data and scoring outputs and produce a human-readable rationale (explanation text) that cites the key rule evaluations and LLM reasoning used to arrive at the score.
- The pipeline must be orchestrated so agents run sequentially in this order: data-fetch agent -> scoring agent -> explainer agent, with each agent receiving the prior agent's output programmatically (no manual copy-paste).
- After the explainer agent completes, the app must write the final credit score and the generated explanation back into the same applicant document in Azure DocumentDB, adding a timestamp and agent metadata (agent names, rule summary, and LLM output snippet) to the document.
- The code must handle missing applicants or Azure DocumentDB errors gracefully: log the error, avoid writing incomplete results back to the database, and return a clear error/status from the pipeline.
- Include an automated test or runnable example that exercises the full pipeline end-to-end against a test Azure DocumentDB dataset and asserts that the final score and explanation were written to Azure DocumentDB for the test applicant.

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
