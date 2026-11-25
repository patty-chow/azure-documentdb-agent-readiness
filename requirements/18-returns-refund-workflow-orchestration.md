# Reference requirements: Returns & refund workflow orchestration

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the sample in Node.js and orchestrate the flow using a LangChain orchestration flow.
- Create three distinct LangChain agents named "policy agent", "refund agent", and "comms agent", and wire them into a single multi-step orchestration that runs policy agent -> refund agent -> comms agent in sequence.
- Fetch the order document from Azure DocumentDB (Microsoft.DocumentDB/mongoClusters) before starting the orchestration and pass that fetched order document as the input to the policy agent.
- Have the "policy agent" return a structured result that includes at minimum: eligibility (boolean) and eligibilityReason (string); if eligibility is false the orchestration must not perform refund calculations and must forward the policy result to the comms agent.
- Have the "refund agent" compute and return a structured numeric refundAmount (and optionally a breakdown such as itemRefunds and shippingRefund) based on the order document and the policy result; refund calculations must be skipped when policy agent marks ineligible.
- Have the "comms agent" generate a structured customer notification that includes customer contact/identifier from the order, eligibility status, refundAmount (if any), eligibilityReason, and a messageBody suitable for notifying the customer; include notificationChannel in the output.
- After orchestration completes, persist a final return document to Azure DocumentDB using Mongoose; the saved document must include orderId, status ("approved", "rejected", or "error"), refundAmount (number, zero if rejected), timestamps, and the raw agent outputs (policyResult, refundResult, commsResult).
- Ensure the flow accepts a return request input (e.g., orderId and return reason), triggers the order fetch + orchestration, and returns the final persisted return document as the API response.
- Implement error handling so that if the order is not found or any agent throws an error, the code writes a return document with status "error" and an error field to Azure DocumentDB via Mongoose, and the API responds with that error-state document.
- Provide runnable tests or a demo script that exercises both an approved return path and a rejected return path, verifying that agent outputs are produced and that final documents are written to Azure DocumentDB via Mongoose with the expected fields.

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
