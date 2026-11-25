# Reference requirements: Market news sentiment orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the pipeline in Node.js with LangChain, with an orchestrator that runs the scraper agent, the sentiment agent and the alert agent in that order and passes each agent's output to the next.
- Implement a scraper agent that fetches financial news headlines and hands the fetched headlines to the orchestrator.
- Implement a sentiment agent that assigns a sentiment score to each fetched headline.
- Have the sentiment agent extract the ticker mentions from each headline alongside its score.
- Store every scored article as a document in Azure DocumentDB using a MongoDB driver for Node.js (e.g. `mongodb`), with each document carrying the headline, its sentiment score and the extracted ticker mentions.
- Implement an alert agent that queries Azure DocumentDB for watchlist entries matching the tickers extracted from the scored headlines.
- Have the alert agent fire a notification for each watchlist match it finds.

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
