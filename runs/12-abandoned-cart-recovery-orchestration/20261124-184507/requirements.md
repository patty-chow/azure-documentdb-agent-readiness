# Reference requirements: Abandoned cart recovery orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the orchestration pipeline in Node.js using a LangChain orchestrator as the central coordinator (entry point file that constructs and runs the LangChain orchestrator).
- Query Azure DocumentDB for carts abandoned for over 2 hours (e.g., lastActivity or updatedAt older than now minus 2 hours) and only return carts not already marked processed; the query must run against Azure DocumentDB.
- Iterate over all qualifying carts (pipeline must process multiple carts in a single run, not only the first result).
- For each cart, invoke a copy-generation agent (named or implemented as a "copy-generation agent" in the LangChain flow) that produces a single personalised recovery message string using customer data (e.g., customer name) and cart contents (item names or summaries).
- Ensure the copy-generation agent’s output (the personalised message) is passed programmatically to the next step in the LangChain orchestrator rather than re-querying the cart.
- Hand off the personalised message and customer record to a channel agent (implemented as a "channel agent" in the LangChain flow) that selects between email or SMS based on the customer's stored preference field (e.g., contactPreference).
- The channel agent must call checkable send functions named sendEmail and sendSMS (or clear provider integration functions) and pass the personalised message plus necessary recipient info; the code must show the channel selection logic invoking sendEmail for email preference and sendSMS for SMS preference.
- Log the outcome of each cart’s attempt back to Azure DocumentDB by inserting or updating a record with at minimum: cartId, personalisedMessage, channelUsed (email or SMS), deliveryResult/status, and timestamp.
- Mark processed carts to avoid duplicate recovery attempts (e.g., set processedAt timestamp or status flag in Azure DocumentDB) as part of the same run after a successful or failed send attempt.
- Capture and persist errors from the copy-generation agent or the channel agent to Azure DocumentDB (error message and stack or provider response), so each cart record reflects success or failure.

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
