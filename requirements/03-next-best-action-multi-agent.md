# Reference requirements: Next-best-action multi-agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the system in Python using LangChain and define four named components: a propensity agent, a channel agent, a timing agent, and an orchestrator (all implemented as LangChain agents/components).
- The propensity agent queries Azure DocumentDB history documents for a given customer_id and returns structured numeric likelihood scores for each action type (e.g., a dict mapping action_type -> score).
- The channel agent reads the customer's preference documents from Azure DocumentDB and returns a single optimal contact channel (e.g., "email", "sms", "push") along with the preference document id used.
- The timing agent analyzes customer interaction timestamps (sourced from Azure DocumentDB history or preference documents) and returns the best send time as an ISO 8601 timestamp (or a consistent datetime object) for the recommended action.
- The orchestrator invokes the propensity, channel, and timing agents via LangChain constructs for a supplied customer_id, merges their outputs, and selects the recommended_action (e.g., highest propensity score) to form the NBA recommendation.
- The NBA recommendation object created by the orchestrator must include at minimum: customer_id, recommended_action, action_scores (from propensity agent), channel (from channel agent), send_time (from timing agent), and created_at timestamp.
- The orchestrator writes the NBA recommendation document into Azure DocumentDB (e.g., a recommendations collection) and returns the inserted document id or the stored document as proof of persistence.
- All reads and writes against customer history and preference documents are performed against Azure DocumentDB (the service) and visibly reference the history and preference document collections in the code.
- Agents must exchange structured data (e.g., Python dicts/JSON) so the orchestrator can combine outputs programmatically, rather than relying on free-form text parsing of agent responses.
- Provide an executable example (entrypoint or script) that runs the orchestrator for a sample customer_id, prints the final NBA recommendation, and demonstrates retrieving the stored recommendation from Azure DocumentDB.

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
