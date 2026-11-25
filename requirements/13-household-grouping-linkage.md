# Reference requirements: Household grouping & linkage

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The service is a Node.js application using Mongoose, with Mongoose models for customer documents and household group documents stored in Azure DocumentDB.
- The service provides an operation that identifies household members by matching customer documents on shared address, phone and surname fields (e.g. an aggregation that groups customers by those field values).
- For each identified household the service creates a household group document that holds references to its member customer documents (e.g. an array of member customer ObjectIds declared with a Mongoose `ref`).
- An HTTP endpoint computes household-level CLV for a given household by running a Mongoose aggregation pipeline on Azure DocumentDB that combines the CLV of all of that household's members (e.g. summing each member's CLV value).
- An HTTP endpoint computes household-level product holdings for a given household by running an aggregation pipeline that combines the products held across all of that household's members (e.g. the distinct set of products with counts).

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
