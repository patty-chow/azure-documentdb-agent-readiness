# Reference requirements: Voice-of-customer sentiment hub

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Python with LangChain to build a single agent that takes each incoming feedback item through the whole flow: ingest, extract, embed and store.
- Accept customer feedback from more than one channel (e.g. email, chat, survey) and carry each item's source channel through to the stored document.
- Use prompt engineering (LangChain prompts sent to an LLM) to extract from each feedback text its sentiment, its key topics and a verbatim quote taken from the original text.
- Compute an embedding of the feedback text (e.g. with a LangChain embeddings integration) and store the resulting vector on the document.
- Define the enriched feedback document as a Beanie ODM model and persist it to Azure DocumentDB through Beanie, holding the original text, the source channel, when the feedback was received, the extracted sentiment, key topics and verbatim quote, and the embedding.
- Build an aggregation pipeline, run in Azure DocumentDB through Beanie's aggregation API, that surfaces a net sentiment measure per channel (e.g. positive minus negative share, or an average sentiment score).
- Build an aggregation pipeline, run in Azure DocumentDB, that surfaces net sentiment per key topic.
- Build an aggregation pipeline, run in Azure DocumentDB, that surfaces net sentiment over time by bucketing feedback into time periods (e.g. per day, week or month) so trends can be reported.

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
