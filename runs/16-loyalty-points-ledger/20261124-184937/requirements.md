# Reference requirements: Loyalty points ledger

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the app in Node.js and use Mongoose as the ODM to model data and query Azure DocumentDB (MongoDB API).
- Define an immutable "events" Mongoose model/collection where every earn and redeem action is stored as its own document (include accountId, type (earn|redeem), amount, timestamp) and mark core event fields as immutable in the schema so events cannot be updated.
- Maintain a separate "balances" Mongoose model/collection that stores the running balance per account; the running balance must only be changed by transactions that also append an event (no direct non-transactional updates).
- When recording an earn or redeem, open a MongoDB session and use multi-document transactions (session.startTransaction / session.commitTransaction / session.abortTransaction) to atomically (a) insert the new event document into the events collection and (b) update the corresponding document in the balances collection so both operations commit or rollback together.
- For redeem operations, enforce within the same multi-document transaction that the resulting running balance does not become negative (transactionally check current balance and abort if insufficient funds).
- Expose an HTTP GET /history endpoint that returns the full event-sourced ledger for a specified accountId, ordered chronologically (oldest first) and read from the events collection (no projection that omits event immutability fields).
- Expose an HTTP GET /balance endpoint that returns the account's current running balance (from the balances collection) and also returns tier status computed from lifetime points.
- Implement a MongoDB aggregation pipeline (using Mongoose .aggregate()) that computes lifetime points as the sum of all "earn" event amounts for an account (ignore redeem events when computing lifetime), maps lifetime points to a tier (e.g., Bronze/Silver/Gold thresholds coded in the pipeline or a $switch), and return that tier in the API response.
- Ensure the /balance endpoint includes the aggregation result (lifetime points and tier) alongside the running balance so the tier is derived from event history via the aggregation, not just from the balances document.
- Demonstrate connection configuration that targets Azure DocumentDB (MongoDB API) in the code (connection usage via Mongoose) so reviewers can confirm the app is written for Azure DocumentDB and uses multi-document transactions supported there.

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
