# Reference requirements: Anti-money laundering pattern detector

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Python with LangChain as a single agent that is given a DocumentDB aggregation tool and invokes that tool to analyse transactions.
- The DocumentDB aggregation tool runs aggregation pipelines against the transaction documents in Azure DocumentDB through a MongoDB driver (e.g. PyMongo's `aggregate`).
- Transactions are modelled as documents that reference other documents (e.g. a counterparty account or a linked transaction), and the aggregation tool follows those references to assemble counterparty chains (e.g. with `$graphLookup` or chained `$lookup` stages).
- Known AML typology rules are expressed as stages of the aggregation pipeline, so the typology matching runs in Azure DocumentDB (e.g. circular transfers, structuring just below a threshold, rapid pass-through of funds).
- Chains that match a typology rule are flagged as suspicious, and the flagged chains are what the tool returns to the agent.
- For each flagged chain the agent generates a structured suspicious activity narrative: an object with defined fields (e.g. a Pydantic model or JSON) that describes the chain and the suspicious pattern it matched.

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
