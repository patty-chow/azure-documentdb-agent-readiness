# Reference requirements: Invoice matching & reconciliation

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the solution in Node.js and instantiate a LangChain agent named exactly "LangChain agent" to coordinate LLM calls, database queries, tools and memory.
- Use Mongoose as the ODM for all database operations; include explicit Mongoose models/schemas for invoices and purchase orders and use those models for reads and writes.
- Connect to Azure DocumentDB (the managed MongoDB‑compatible service) via Mongoose using a MongoDB connection URI so all reads/writes go to Azure DocumentDB.
- Read only unmatched invoices from Azure DocumentDB by querying the invoices collection for an "unmatched" state (e.g., a field such as status == "unmatched") and iterate those documents for reconciliation.
- Extract structured invoice fields by invoking an LLM extraction tool (the prompt’s "LLM extraction tool") from within the LangChain agent; the extraction must produce at minimum: invoiceNumber, vendorName, totalAmount, invoiceDate, lineItems, and any referencedPoNumber.
- Search the Azure DocumentDB purchase orders collection for candidate PO matches by amount and vendor: query POs whose amount is within a configurable tolerance of the extracted totalAmount and that match vendor criteria.
- Implement fuzzy document/vendor comparison (e.g., a fuzzy string similarity algorithm) to compute a vendor similarity score for each candidate PO and include fuzzy comparison for relevant invoice text where appropriate.
- Compute a combined numeric match score for each candidate PO that combines vendor similarity and amount difference (and whether an explicit PO number was present); include a score breakdown (vendorScore, amountDelta, combinedScore) for reviewer inspection.
- Sort candidate POs by combined score and select or rank top candidates; include enough candidate metadata so a human can inspect why a match was chosen.
- Write reconciliation results back to Azure DocumentDB: update the invoice document (or create a reconciliation record) with matchedPoId (if any), matchScore, matchDetails (vendorScore, amountDelta, score breakdown), matchedAt timestamp, and set the invoice status to "matched" upon successful reconciliation.
- Support manual corrections during a session by exposing a callable/manual-correction path that the LangChain agent records into its agent memory (exactly "agent memory"), and require that subsequent matching decisions in the same session consult that in‑memory correction so the agent “learns” and prefers corrected mappings; memory updates must be session-scoped (not automatically persisted across sessions unless explicitly implemented).

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
