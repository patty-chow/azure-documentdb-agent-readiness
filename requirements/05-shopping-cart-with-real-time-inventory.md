# Reference requirements: Shopping cart with real-time inventory

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose ODM to model and persist Cart and Inventory documents in Azure DocumentDB (connections and models must target Azure DocumentDB).
- Define an Inventory schema that includes a numeric stock field and a numeric version field used for optimistic locking.
- Define a Cart schema that can store userId and an items array (productId and quantity) in Azure DocumentDB.
- Implement an add-to-cart function that starts a Mongoose session (startSession()) and begins a DocumentDB multi-document transaction (session.startTransaction()) before making any updates.
- Within the same session, perform the inventory decrement and the cart insert/update so both operations execute inside the DocumentDB multi-document transaction and pass the session to all Mongoose operations.
- Decrement inventory using a conditional update that enforces both available stock and the current version (e.g., filter includes version and stock >= qty) and atomically increments the version in the same update so optimistic locking is enforced by the version field.
- Apply the cart change (insert or update item quantities) within the same transaction session so the inventory change and cart change are committed or aborted together.
- Commit the transaction on success (session.commitTransaction()) and abort/rollback on any failure (session.abortTransaction()), and properly end the session.
- Detect and handle optimistic-lock conflicts (zero documents matched due to version mismatch) by retrying a configurable number of times or returning a specific conflict error if retries are exhausted.
- When requested quantity exceeds available stock, return a clear, programmatic out-of-stock error (distinct message or error code) and ensure no decrement or cart add is committed.
- Include an automated integration test or concurrency simulation that issues parallel add-to-cart requests and asserts that no overselling occurs (inventory never drops below zero and total reserved items do not exceed initial stock).

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
