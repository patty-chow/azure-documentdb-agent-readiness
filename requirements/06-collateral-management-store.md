# Reference requirements: Collateral management store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the service in Node.js using the Mongoose ODM to persist documents to Azure DocumentDB (MongoDB-compatible endpoint) and include the connection/config code in the repository.
- Define a Mongoose schema for collateral documents that includes a stable logical assetId, a numeric version field, a createdAt timestamp, and a schemaVersion field; every persisted document must include all four fields.
- On every asset creation or valuation update, persist a new document (do not overwrite prior documents) in Azure DocumentDB with an incremented version value and a createdAt timestamp so prior versions are retained for full audit history.
- Ensure each versioned document stores valuation and pledge-related fields (e.g., currentValuation, pledgedAmount) necessary to compute coverage, and keep the logical assetId constant across versions to link them.
- Add an LLM classification step that runs on create and on every valuation update and writes classification results into the document fields type and eligibilityTier before persisting the new version.
- Provide an HTTP endpoint that returns the full audit history (all versions) for a given assetId by querying Azure DocumentDB and ordering by version or createdAt.
- Provide an HTTP aggregation endpoint that computes and returns the total collateral coverage ratio by running a MongoDB aggregation (via Mongoose) over Azure DocumentDB: sum of currentValuation across relevant documents divided by sum of pledgedAmount; clearly return totalCollateralValue, totalPledgedAmount, and coverageRatio and handle division-by-zero (e.g., return null or Infinity as documented).
- The aggregation endpoint must use stored versioned documents to compute totals (e.g., use the latest version per asset or clearly document which versions are aggregated) and the code must show the aggregation pipeline used to produce the ratio.
- Include tests or example requests demonstrating: creating an asset, performing a valuation update that creates a new version and receives type and eligibilityTier tags, retrieving that asset’s audit history, and calling the aggregation endpoint to obtain the total collateral coverage ratio.

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
