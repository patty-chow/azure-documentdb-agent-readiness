# Reference requirements: Preference center & consent store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Python FastAPI service exposes HTTP endpoints to record consent, withdraw consent, and retrieve a customer's current preference state (e.g. POST to record, POST to withdraw, GET to retrieve).
- Customer consent records and channel preferences are modelled as Beanie ODM Document classes and stored as documents in Azure DocumentDB.
- Each consent document carries a consentVersion field and a consent history sub-array that holds past consent events for audit.
- Recording consent appends a new entry to the consent history sub-array (e.g. with a push update that leaves earlier entries in place) and updates the document's current channel preferences and consentVersion.
- Withdrawing consent appends a new entry to the consent history sub-array (e.g. with a push update that leaves earlier entries in place) and updates the document's current channel preferences.
- The retrieve endpoint reads the customer's document from Azure DocumentDB through Beanie and returns its current preference state.
- A TTL index with expireAfterSeconds is created in code (e.g. in the Beanie Document's index settings) on a Date-typed retention field of the consent documents, for data retention enforcement.
- Consent documents written by the record and withdraw endpoints set that Date-typed retention field.

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
