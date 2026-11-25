# Reference requirements: Trade settlement tracker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Define a Mongoose model in Node.js (stored in Azure DocumentDB) named e.g. "Trade" whose documents include: tradeId, assetClass, counterparty, state (enum containing at least "matched", "settled", "failed"), and an eventLog array to record transition events.
- Ensure new trades are created with initial state "matched" (i.e., creation code sets state: "matched").
- Implement a state-transition function in Node.js using Mongoose that opens a MongoDB session (startSession) and uses a transaction (session.withTransaction or equivalent) to atomically update the trade's state and perform other writes within the same transaction.
- Within that transaction, atomically push a transition event into eventLog and update the trade's state in the same transaction so the state change and its event are committed together.
- Each transition event appended to eventLog must include at least: fromState, toState, timestamp, and a reason/actor field so reviewers can verify transitions are logged with those attributes.
- Enforce state-machine rules in the transition function (e.g., only allow valid transitions such as matched -> settled or matched -> failed); reject or throw when an invalid transition is attempted.
- Open a change stream on the Trade collection (using the MongoDB change stream API via Mongoose/driver) and detect updates where the trade's state becomes "failed" (inspect updateDescription or fullDocument state change).
- When the change stream detects a state change to "failed", trigger an exception workflow implemented in the app; the workflow must perform a verifiable side effect in Azure DocumentDB (for example, insert an "Exception" document with tradeId, timestamp, and failure reason).
- Expose an HTTP aggregation endpoint (e.g., Express GET /settlement-rates) implemented in Node.js that runs a MongoDB aggregation pipeline (via Mongoose/collection.aggregate) grouping by assetClass and counterparty and returns settlement rates (settled_count / total_count) for each group.
- Provide a replay/reconstruction function that derives a trade's current state by replaying its eventLog (demonstrable via a unit test or an endpoint), showing the system implements event-sourcing semantics for trade state.

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
