# Reference requirements: Omnichannel interaction history

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- The service is written in Node.js and uses the Mongoose ODM: one Mongoose schema and model describes a customer interaction document, and that model is backed by a single Azure DocumentDB collection that holds interactions from every channel (web, mobile, email, call centre).
- The interaction schema has channel, customerId and timestamp fields, with channel identifying the source of the interaction; other interaction content may be carried alongside them.
- Interactions from any channel are stored through that same model (e.g. a create endpoint or model method that saves an interaction document).
- A compound index on (customerId, timestamp) is declared in application code on the Mongoose schema (e.g. schema.index({ customerId: 1, timestamp: -1 })) and created on the Azure DocumentDB collection by the application (e.g. via Mongoose autoIndex when the model initialises, or syncIndexes()/createIndexes() at startup).
- A compound index on (channel, timestamp) is declared in application code on the same Mongoose schema and created on the same Azure DocumentDB collection by the application.
- The history endpoint returns a customer's interactions filtered by customerId and sorted by timestamp, and is paginated: each call returns one page (e.g. limit with skip, or a cursor on timestamp) and the caller can request the next page.
- The channel-breakdown endpoint runs a Mongoose aggregation pipeline (Model.aggregate) in Azure DocumentDB that groups interactions by channel and returns a per-channel summary (e.g. a count for each channel, optionally scoped to one customerId).

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
