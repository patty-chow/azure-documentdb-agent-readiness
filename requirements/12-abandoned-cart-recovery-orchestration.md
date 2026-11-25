# Reference requirements: Abandoned cart recovery orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A Node.js LangChain orchestration pipeline runs the recovery flow as one sequence per run: query abandoned carts, copy-generation agent, channel agent, outcome logging.
- The pipeline queries Azure DocumentDB through a Node.js MongoDB driver (e.g. the `mongodb` package) for carts abandoned for over 2 hours, comparing each cart's abandonment time against a threshold two hours before the current time (e.g. a `$lt` on the cart's last-activity timestamp).
- Each cart the query returns is passed to a LangChain copy-generation agent that produces a personalised recovery message using that cart's contents and customer details.
- The copy-generation agent hands off to a LangChain channel agent, passing the generated message together with the cart it was written for.
- The channel agent reads the customer's stored channel preference and sends the message by email when the preference is email and by SMS when it is SMS, through two distinct delivery paths.
- After each send, the outcome is written back to Azure DocumentDB (e.g. a recovery-log document, or an update on the cart, recording the channel used and whether the send succeeded).

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
