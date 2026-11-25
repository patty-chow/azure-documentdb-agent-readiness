# Reference requirements: Omnichannel interaction history

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Use Node.js and Mongoose to connect to Azure DocumentDB (MongoDB-compatible endpoint) and open a single database connection for the service.
- Define one Mongoose model (single collection) for all channels (e.g., "interactions") with required fields channel (String), customerId (String), timestamp (Date) and a flexible field for channel-specific payload (Mixed/Map); ensure all documents for web, mobile, email and call centre are stored in this collection.
- Create compound indexes on the schema using schema.index(...) for { customerId: 1, timestamp: -1 } and { channel: 1, timestamp: -1 } so the compound indexes exist in Azure DocumentDB.
- Implement an HTTP ingestion endpoint that validates and writes interaction documents into the single collection, enforcing presence and types of channel, customerId and timestamp and storing timestamp as a Date/ISODate.
- Expose a paginated history HTTP endpoint that returns interactions filtered by either customerId or channel (one required), accepts pagination params (page & pageSize or limit & skip), optional startTimestamp and endTimestamp query params, and sorts results by timestamp.
- Ensure the paginated history query builds a Mongo query that includes the customerId (when provided) or channel (when provided) plus a timestamp range filter so the query can use the appropriate compound index, and implement pagination via limit/skip (or cursor) and sort on timestamp.
- Expose a channel-breakdown aggregation HTTP endpoint that accepts customerId and optional time range and returns counts grouped by channel using a MongoDB aggregation pipeline ($match by customerId and timestamp range, then $group by channel, $count or $sum).
- Ensure aggregation pipelines include the $match stage(s) on customerId and timestamp range (and channel when supplied) so the pipeline can leverage the (customerId, timestamp) or (channel, timestamp) compound indexes as appropriate.
- Parse timestamp query parameters into Date objects before querying and store/query timestamps as Date types so range queries behave correctly against the timestamp field.

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
