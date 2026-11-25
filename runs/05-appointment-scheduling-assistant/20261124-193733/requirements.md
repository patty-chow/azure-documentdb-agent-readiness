# Reference requirements: Appointment scheduling assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- A single Node.js agent built with LangChain lets a patient book, reschedule and cancel appointments through conversation, choosing which of its tools to call for each request.
- The agent has agent memory that carries the conversation context across turns, so a follow-up such as "move it an hour later" is resolved against the appointment discussed earlier without the patient restating the provider, date or time.
- A LangChain tool queries provider availability slots from Azure DocumentDB each time the agent needs availability, reading the current slot documents through a MongoDB-compatible Node.js driver (e.g. the `mongodb` package).
- Provider availability is modelled as slot documents in Azure DocumentDB, each carrying a status that the booking and rescheduling tools change (e.g. available to booked).
- A tool books an appointment by creating an appointment document in Azure DocumentDB for the chosen slot and updating that slot's status.
- A tool reschedules an existing appointment by updating slot status atomically (e.g. a single conditional update that claims the new slot only while it is still available, or a session `withTransaction` when the old slot, the new slot and the appointment document change together) and pointing the appointment document at the new slot.
- When a patient gives a relative time such as "an hour later", the agent computes the target time from the remembered appointment time and uses the availability tool to find a matching slot in Azure DocumentDB before rescheduling.
- A tool cancels an appointment by updating the appointment document in Azure DocumentDB and returning its slot to an available status.

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
