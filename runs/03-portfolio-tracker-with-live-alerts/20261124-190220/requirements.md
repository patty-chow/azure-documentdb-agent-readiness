# Reference requirements: Portfolio tracker with live alerts

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB via a MongoDB-compatible connection string supplied by an environment variable (connection established with Mongoose.connect).
- Provide Mongoose models for the positions collection and the alert rules collection (models named e.g., Position and AlertRule) with fields sufficient to evaluate alerts (positions: userId, symbol, shares, avgCost, currentPrice, sector, updatedAt; alert rules: userId, scope (symbol or global), metric (e.g., "price" or "pnl"), comparison (">","<"), threshold, webhookUrl, active).
- Open a change stream on the positions collection using the Azure DocumentDB change streams feature (use positions.watch(...) via Mongoose/driver) and configure the stream to retrieve the latest document (fullDocument: "updateLookup").
- Detect relevant price updates by inspecting change stream events and only trigger evaluation when the event shows a price change (e.g., operationType "update" with updateDescription.updatedFields.currentPrice present, or an "insert" with a currentPrice).
- For each position change that passes the price-change detection, query the alert rules collection for active rules applicable to that position (match by userId and symbol or by global scope) and evaluate each rule's condition against the updated position document (support at least metric types "price" and "pnl" where pnl = (currentPrice - avgCost) * shares).
- When a rule is breached, send an HTTP POST webhook to the alert rule's webhookUrl with a JSON payload that includes the position document, the alert rule document, the breached metric name and value, and a UTC timestamp; implement the POST using a Node.js HTTP client (e.g., fetch or axios) and record the webhook HTTP status in logs or collection.
- Implement an aggregation pipeline (using Mongoose aggregate) that computes for a given user: total portfolio P&L as sum((currentPrice - avgCost) * shares) and sector allocation as per-sector total market value (marketValue = currentPrice * shares) with each sector's percentage of the portfolio total.
- Expose the aggregation via an HTTP endpoint (e.g., GET /portfolio/:userId/summary) that returns a JSON object containing total P&L and an array of sectors with their marketValue and percentage allocation computed by the aggregation.

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
