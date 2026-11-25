# Reference requirements: Invoice matching & reconciliation

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a single LangChain agent in Node.js that carries each invoice through the whole flow: read the invoice, extract its fields, search for candidate purchase orders, score them and write the result back.
- Read unmatched invoices from Azure DocumentDB through Mongoose models (e.g. invoices that have no reconciliation result yet).
- Expose field extraction as an LLM-backed tool the agent calls, returning structured fields from the invoice (e.g. vendor, total amount, invoice number) that the later steps use.
- Query Azure DocumentDB through Mongoose for candidate purchase orders using the extracted amount and vendor.
- Score each candidate purchase order against the invoice (e.g. by vendor-name similarity and amount closeness) and choose the match from those scores.
- Write the reconciliation result for the invoice back to Azure DocumentDB through Mongoose.
- Keep agent memory for the session that records manual corrections (e.g. a user overriding the chosen PO) and consult it when matching later invoices in the same session.

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
