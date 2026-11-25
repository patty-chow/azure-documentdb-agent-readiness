# Reference requirements: Customer journey mapper

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Build the application in Node.js as a single LlamaIndex agent that owns the whole flow: it invokes the aggregation tool, formats the result into its prompt and produces the final summary.
- The agent takes the customer whose journey is to be mapped as its input (e.g. a customer identifier) and passes it to the aggregation tool.
- Register a DocumentDB aggregation tool with the LlamaIndex agent that runs an aggregation pipeline (e.g. with the `mongodb` Node.js driver) over the touchpoint event documents stored in Azure DocumentDB for that customer.
- The pipeline itself reconstructs the journey: it sorts the customer's events by timestamp and groups them by channel (e.g. a `$match` on the customer, a `$sort` on the timestamp and a `$group` by channel).
- Apply context engineering to the tool's output: format the reconstructed journey as a structured timeline (e.g. events in chronological order, each labelled with its channel and timestamp) and place that formatted timeline in the prompt sent to the model.
- The agent generates a plain-language summary of the customer's journey from the timeline in its prompt.
- The summary highlights key inflection points in the journey (e.g. a first purchase, a long gap in activity or a switch between channels), marked so they stand out from the rest of the narrative.

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
