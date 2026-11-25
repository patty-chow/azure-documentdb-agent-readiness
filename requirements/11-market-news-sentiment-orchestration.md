# Reference requirements: Market news sentiment orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and LangChain to implement an Orchestration pipeline that composes three agents named scraper agent, sentiment agent, and alert agent, with a LangChain orchestrator coordinating their execution.
- Implement the scraper agent to fetch live financial news headlines over HTTP (RSS, news API, or scraping) and return for each item an object containing at minimum: headline text, source, and timestamp.
- Implement the sentiment agent to accept a headline and return a numeric sentiment score and an array of extracted ticker symbols (e.g., ["AAPL","MSFT"]); outputs must be typed/structured values (not just console text).
- Implement the alert agent to query Azure DocumentDB for a watchlist collection and determine matches by exact ticker symbol comparison between extracted tickers and watchlist entries.
- When a watchlist match occurs, the alert agent must fire a notification by sending a JSON payload that includes the article unique id, headline, matched ticker(s), and sentiment score to a configurable webhook (or other pluggable notification target); notifications must be observable in runtime logs or outgoing requests.
- Persist every scored article as a document in Azure DocumentDB in a dedicated collection (e.g., "sentiment_signals"); each document must include a unique id, headline, numeric sentiment score, extracted tickers array, source, and timestamp.
- Use Azure DocumentDB for both the stored signals/articles collection and the watchlist collection—all reads and writes for those features must go to Azure DocumentDB (not to in-memory stores or other databases).
- Structure the code so each agent is a separate module/function/class and the LangChain orchestrator explicitly invokes the scraper agent → sentiment agent → store in Azure DocumentDB → alert agent sequence for each headline.
- Make Azure DocumentDB connection parameters (connection string/URI and database/collection names) and the notification webhook endpoint configurable (for example via environment variables) so a reviewer can run the pipeline against a test Azure DocumentDB instance.
- Include an end-to-end demo or test script that runs the pipeline on at least one scraped headline, shows the sentiment score and extracted tickers, verifies the document was written into Azure DocumentDB, and demonstrates an alert firing when a ticker is present in the watchlist.

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
