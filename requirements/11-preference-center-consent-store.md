# Reference requirements: Preference center & consent store

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Python and FastAPI and persist data with Beanie ODM to Azure DocumentDB (MongoDB-compatible) — the codebase must include a Beanie Document model and show it being used with FastAPI route handlers.
- Define a Beanie Document model for customer consent/preference documents that includes a top-level consentVersion field and a channel preferences structure (e.g., per-channel booleans or enum states) stored as fields on the Document.
- Include an append-only consent history sub-array on the same Beanie Document model; each history entry must include at minimum a timestamp, consentVersion, channel states, and an event type (e.g., "grant" or "withdraw").
- The record-consent endpoint must append a new entry to the consent history sub-array and update the top-level current preference snapshot and consentVersion in a single atomic operation (e.g., a single $push plus $set-style update via Beanie/Mongo update APIs).
- The withdraw-consent endpoint must append a withdrawal event to the consent history sub-array (do not modify or delete prior history entries) and update the top-level current preference snapshot and consentVersion to reflect withdrawn status in the same atomic update.
- The retrieve-current-preferences endpoint must return the current preference state and consentVersion (a snapshot stored on the document or derived deterministically from the latest history entry) without exposing or modifying prior history entries.
- Create and register a TTL index (DocumentDB TTL index) on a document-level retention timestamp field (e.g., expiresAt or retentionExpiresAt) and ensure code sets that field when writing records so Azure DocumentDB will automatically expire documents according to the retention policy.
- Ensure the API and data model enforce append-only audit behavior: there must be no route or code path that mutates or removes existing entries inside the consent history sub-array (history entries are only added).
- Include example request/response shapes or FastAPI route implementations for the three required endpoints (record consent, withdraw consent, retrieve current preference state) so a reviewer can exercise them against an Azure DocumentDB instance.

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
