# Reference requirements: Shopping cart with real-time inventory

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the cart service in Node.js using the Mongoose ODM, with Mongoose schemas and models for cart documents and inventory documents stored in Azure DocumentDB.
- Provide a cart-service operation that adds an item to a cart and decrements that item's stock in the inventory document.
- Run the stock decrement and the cart addition inside one Azure DocumentDB multi-document transaction on a session (e.g. `session.withTransaction`, or `startTransaction` / `commitTransaction` / `abortTransaction`), passing the session to every Mongoose read and write that takes part in the operation.
- Check stock inside the transaction, so the decrement only applies when the inventory document holds at least the requested quantity (e.g. a conditional update that filters on the current stock value).
- Keep a version field on the documents the operation updates, at minimum the inventory document, for optimistic locking (e.g. Mongoose's `versionKey` / `__v` or a custom field): an update filters on the version it read and increments the version when it succeeds.
- When the version check fails because the document changed since it was read, the operation reports a conflict to the caller or retries the update instead of overwriting the newer document.
- When stock is exhausted, abort the transaction and surface a clear error to the caller that identifies the out-of-stock condition (e.g. a dedicated error type or message), distinct from other failures.

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
