# Reference requirements: Proactive outreach orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Node.js using LangChain as an orchestration pipeline: code must instantiate an orchestrator agent that coordinates three agents named trigger agent, copy agent, and send agent.
- The trigger agent must use DocumentDB change streams (the DocumentDB change streams feature) against Azure DocumentDB via the MongoDB Node.js driver to subscribe to changes on the relevant collections.
- The trigger agent must detect and emit specifically the three qualifying customer events (cart abandon, contract renewal, birthday) with explicit, checkable detection logic for each event type (e.g., cart inactivity or abandoned cart conditions; renewal date within X days; customer DOB matching today's date).
- When a trigger event is detected the code must pass the full event document to the copy agent through the LangChain orchestration flow (i.e., the orchestrator invokes the copy agent with the event payload).
- The copy agent must retrieve additional context from Azure DocumentDB (customer profile, order/cart contents, contract details, recent interactions) and use context engineering: assemble a templated prompt that injects those context fields and call an LLM through LangChain in Node.js to generate the personalised outreach copy.
- The send agent must read the customer's preferred channel from the customer profile stored in Azure DocumentDB and invoke the appropriate channel adapter implementation (email, SMS, push, etc.) in Node.js; the code must include channel-specific send functions or adapters and clear selection logic.
- All outcomes must be logged back to Azure DocumentDB: the pipeline must write a log document to a dedicated collection (for example "outreach_logs") containing the original event, generated copy, selected channel, send result (success/failure and any provider message IDs or errors), and timestamps using the MongoDB Node.js driver.
- The orchestration must be end-to-end observable: running the sample must demonstrate that a simulated or real change-stream event flows trigger -> copy -> send -> log, and the code must include a runnable entrypoint or script that starts the orchestrator and demonstrates one end-to-end event.
- Provide example configuration/fixtures in the sample that allow a reviewer to exercise the three event types (sample change-stream event documents or a script that writes test events to Azure DocumentDB), so the reviewer can verify detection, personalized copy generation, channel dispatch, and logging.

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
