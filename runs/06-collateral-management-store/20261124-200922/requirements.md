# Reference requirements: Collateral management store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js collateral management service defines Mongoose schemas for collateral assets and their valuations and stores them in Azure DocumentDB.
- Each collateral asset and each valuation update is saved as its own document carrying a version field and a createdAt timestamp.
- Saving an update for an existing asset writes a new document with a higher version number, and the earlier versions remain in the collection as the asset's history.
- An LLM classification step tags each stored asset with an asset type and an eligibility tier.
- An HTTP endpoint returns the total collateral coverage ratio, computed with a Mongoose aggregation pipeline that runs in Azure DocumentDB.
- The coverage calculation uses only the most recent version of each asset's valuation (e.g. the highest version or latest createdAt per asset).

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
