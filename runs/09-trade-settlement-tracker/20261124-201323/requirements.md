# Reference requirements: Trade settlement tracker

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js application uses the Mongoose ODM to store each trade as a single document in Azure DocumentDB that carries the trade's current settlement state, so one document represents the trade's whole settlement lifecycle (e.g. from matched through to settled or failed).
- The settlement lifecycle is modelled as a state machine: the set of states (e.g. matched, settled, failed and any intermediate ones) and the transitions allowed between them are defined in code, and advancing a trade moves it along one of those transitions.
- Advancing a trade's state runs inside a multi-document transaction on a Mongoose session (withTransaction, or start/commit/abort) so the state change commits atomically.
- Every state transition is logged as a record written within the same transaction as the state change (e.g. a transition document recording which trade moved, from which state to which, and when).
- The application opens a change stream on the trade documents in Azure DocumentDB (Mongoose watch) and detects trades whose settlement has moved to the failed state.
- When the change stream detects a failed settlement, it triggers an exception workflow for that trade (e.g. a handler that records the exception or hands the trade to a follow-up process).
- An HTTP endpoint runs an aggregation pipeline in Azure DocumentDB that returns settlement rates grouped by asset class and by counterparty (e.g. the share of trades that reached settled out of all trades in each group).

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
