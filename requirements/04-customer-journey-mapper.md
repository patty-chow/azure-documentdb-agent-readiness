# Reference requirements: Customer journey mapper

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the agent in Node.js and use LlamaIndex as the agent framework (code entrypoint and orchestration must be Node.js and LlamaIndex).
- Add a "DocumentDB aggregation tool" module that executes a MongoDB aggregation pipeline against Azure DocumentDB (MongoDB-compatible API) and is callable by the LlamaIndex agent.
- The aggregation pipeline must accept a customer identifier (customer_id) and optional time-range parameters, and use $match to filter event documents for that customer and range.
- The aggregation pipeline must sort events by their timestamp (ascending) and group events by channel, returning a structure that preserves chronological order across channels (e.g., using $sort plus $group/$push or equivalent pipeline stages).
- The aggregation result returned by the DocumentDB aggregation tool must include, for each touchpoint event, at minimum: timestamp, channel, event_type, and a metadata/object field for additional attributes.
- Use context engineering to format the reconstructed journey as a structured timeline (a machine-readable structure such as JSON or a clearly delimited nested list) and embed that structured timeline in the prompt/context sent to LlamaIndex.
- The LlamaIndex agent must consume the structured timeline from the prompt and generate a plain-language journey summary that explicitly highlights key inflection points.
- The generated plain-language summary must identify and highlight demonstrable inflection points such as channel switches, conversion events (e.g., purchase or signup), and significant inactivity or sudden changes in engagement.
- Produce a visual timeline view (for example an HTML timeline endpoint or file) that renders the reconstructed journey grouped by channel and annotated with timestamps and event labels, derived directly from the aggregation results.
- Provide a runnable example or script that performs an end-to-end run: query a sample customer_id, call the DocumentDB aggregation tool, feed the structured timeline to the LlamaIndex agent, and output both the visual timeline and the plain-language summary; the example must assert that the timeline is chronologically ordered and that the summary contains at least one highlighted inflection point.

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
