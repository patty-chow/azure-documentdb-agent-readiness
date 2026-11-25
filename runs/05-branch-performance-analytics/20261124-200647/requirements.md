# Reference requirements: Branch performance analytics

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python FastAPI service exposes HTTP endpoints for a branch performance dashboard, and the dashboard metrics it serves are computed by aggregation pipelines run in Azure DocumentDB through a MongoDB driver (e.g. PyMongo).
- The aggregation pipeline contains a $facet stage whose sub-pipelines compute transaction volume, average ticket size and product mix, each broken down per branch.
- The per-branch roll-ups produced by the $facet aggregation are written to Azure DocumentDB as cached summary documents (e.g. one document per branch in a summaries collection).
- Dashboard requests for a branch's metrics are served by reading its cached summary document from Azure DocumentDB, with the $facet aggregation run to produce or refresh the summaries.
- A LangChain tool (Python LangChain) takes an analyst's natural-language question and queries the cached summary documents in Azure DocumentDB to answer it.
- The tool is attached to a LangChain agent or chain so that an analyst can submit a natural-language question (e.g. through a FastAPI endpoint) and receive a natural-language answer derived from the cached summaries.

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
