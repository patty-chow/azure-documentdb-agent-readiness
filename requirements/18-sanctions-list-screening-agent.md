# Reference requirements: Sanctions list screening agent

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the screening agent in Python with LangChain as a single agent that takes a screening request (a customer or transaction record) and carries it through searching, consolidation, scoring and the report.
- Store sanctions list entries as documents in Azure DocumentDB with each entry's embedding held on the document, and create a cosmosSearch vector index (kind vector-ivf, vector-hnsw or vector-diskann) on the embedding field in code through a MongoDB driver (e.g. PyMongo), with dimensions matching the embedding model used.
- On each screening request, embed the request with the same embedding model and run a vector similarity search in Azure DocumentDB with $search / cosmosSearch, returning the top candidate entries and their similarity scores.
- On each screening request, also run $regex-based fuzzy matching queries against the sanctions entries' text fields (e.g. name) in Azure DocumentDB and return the matching entries as candidates.
- Consolidate the vector search results and the $regex results into a single set of candidate matches for the request.
- Score each candidate match, producing a match confidence that draws on the vector similarity result and the $regex match evidence.
- Return a structured screening report (e.g. a typed object or JSON) listing each candidate match with its match confidence and a recommended action.

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
