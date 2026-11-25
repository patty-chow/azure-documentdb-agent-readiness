# Reference requirements: Anti-money laundering pattern detector

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python and use LangChain as the agent framework (single-agent) to orchestrate queries and narrative generation.
- Implement and register a DocumentDB aggregation tool that the LangChain agent calls to execute aggregation pipelines against Azure DocumentDB; the tool must accept a target database/collection and an aggregation pipeline and return pipeline results.
- Connect the DocumentDB aggregation tool to Azure DocumentDB (transactions collection) via configurable connection parameters so the tool can run live aggregations against the cluster.
- Build counterparty chains by following transaction document references (transaction reference fields) using graph-like aggregation (e.g., a $graphLookup-style stage) with a configurable max traversal depth, returning full chains of transaction documents and the reference paths between them.
- Ensure the aggregation pipeline preserves key transaction fields needed for analysis (at minimum: transactionId, from/to party IDs, amount, timestamp, and reference fields) in the returned chain documents so the agent can cite source documents.
- Implement multiple known AML typology rules applied via aggregation logic (at least two), for example: circular-flow/cycle detection and rapid value movement across consecutive transactions; each typology must be codified as aggregation stages or post-aggregation filters that mark matched chains.
- Flag chains as suspicious when typology criteria are met and include metadata in the flagged result indicating which typology rule(s) matched and the evidence (e.g., matched transaction IDs, counts, summed amounts, time windows).
- For every flagged chain, have the LangChain agent generate a structured suspicious activity narrative (JSON/dict) that includes: chain summary, involved counterparties and roles, timestamps and amounts overview, typology(s) matched, why the chain was flagged (evidence), and references to the source Azure DocumentDB document IDs used as evidence.
- Expose a programmatic agent interface (method/command) to run detection for a given anchor (transaction ID or account ID) and return the list of flagged chains with their structured suspicious activity narratives.
- Provide an example script or notebook that demonstrates end-to-end usage: seeding or querying sample transactions, invoking the LangChain agent which calls the DocumentDB aggregation tool, and printing the aggregation results plus the generated structured narratives.

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
