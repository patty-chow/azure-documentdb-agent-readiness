# Reference requirements: Proactive outreach orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A trigger agent, written in Node.js, opens a change stream against Azure DocumentDB (e.g. `watch()` through the MongoDB Node.js driver) and keeps listening so customer events are handled as they arrive.
- The trigger agent passes on only qualifying customer events, recognising the three kinds the prompt names: cart abandon, contract renewal and birthday.
- An orchestrator built with LangChain in Node.js coordinates the three agents, handing each qualifying event from the trigger agent to the copy agent and the copy agent's output to the send agent, in that order.
- A copy agent generates personalised outreach copy for the event with a LangChain LLM call.
- The copy agent practises context engineering: its prompt is assembled from the triggering event's details and the customer's data (e.g. profile fields read from Azure DocumentDB), so the copy is personalised to the customer and the event type.
- A send agent determines the customer's preferred channel from their data and dispatches the generated copy through that channel (e.g. email, SMS or push).
- The outcome of each outreach (e.g. the event, the channel used and whether the dispatch succeeded) is written to an Azure DocumentDB collection.

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
