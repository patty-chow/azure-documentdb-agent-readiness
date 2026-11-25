# Reference requirements: Voice-of-customer sentiment hub

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a single-agent application in Python using LangChain that orchestrates ingestion, enrichment (LLM extraction + embeddings), and storage of feedback records.
- Define a persistent document model using Beanie ODM (e.g., FeedbackDocument) and include at minimum these fields: channel (string), original_text (string), sentiment_label (string), sentiment_score (numeric), topics (list[string]), verbatim_quote (string), embedding (list[float]), timestamp (datetime), and metadata (object).
- Initialize Beanie to connect to an Azure DocumentDB instance (Mongo-compatible connection) and demonstrate the Motor/Beanie client pointed at the Azure DocumentDB database used by the sample.
- Provide explicit LangChain prompt templates (prompt engineering) and code that calls them to extract sentiment, key topics, and a verbatim quote from an input feedback text; show parsing/normalization of the LLM output into the Beanie document fields.
- Produce both a categorical sentiment_label and a numeric sentiment_score per feedback item (the numeric score must be stored and used for aggregation).
- Use LangChain's embeddings interface to embed the enriched feedback text (or selected fields) and store the resulting embedding vector in the Beanie document's embedding field.
- After enrichment and embedding, persist the enriched document to Azure DocumentDB via Beanie ODM save/insert operations.
- Implement MongoDB aggregation pipelines (invoked from Python) that compute net sentiment trends by channel, by topic, and by time period (supporting at least daily and weekly buckets); each pipeline must return net sentiment metric (e.g., average sentiment_score) and document counts.
- Expose Python functions or callable routines that run the aggregation pipelines with parameters for channel(s), topic(s), time range, and time-bucket granularity and return results formatted for reporting/visualization.
- Include ingestion handlers and examples for feedback from multiple channels (at least two distinct channels such as "email" and "chat" or "twitter"), ensuring the channel value is recorded on stored documents.
- Provide runnable example scripts or tests that ingest sample feedback items, run the enrichment (prompt + embedding), persist them to Azure DocumentDB, and execute the aggregation pipelines to demonstrate expected trend outputs.

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
