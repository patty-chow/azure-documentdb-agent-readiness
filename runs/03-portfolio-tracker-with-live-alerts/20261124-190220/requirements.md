# Reference requirements: Portfolio tracker with live alerts

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js portfolio service built with Mongoose that defines models for positions and for alert rules and persists documents of both kinds in Azure DocumentDB.
- A change stream opened through Mongoose on the positions collection (e.g. `Model.watch()`) that stays open while the service runs and receives the collection's change events.
- Incoming change events are inspected to detect price updates on positions, and each detected price update triggers alert evaluation for the affected position.
- On a detected price update, each alert rule document is evaluated against the position's new price to decide whether the rule's threshold is breached.
- When an alert rule's threshold is breached, the service fires a webhook (an HTTP request to a webhook endpoint) carrying the alert.
- An aggregation pipeline run through Mongoose on the positions data that computes portfolio P&L (profit and loss) and sector allocation.

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
