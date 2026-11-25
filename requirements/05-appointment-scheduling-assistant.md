# Reference requirements: Appointment scheduling assistant

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement the application in Node.js and build the conversational agent using the LangChain agent framework.
- Expose LangChain Tools that query Azure DocumentDB in real time for provider availability slots (i.e., a tool that queries the slots collection filtering by providerId, time range, and status 'available'); the tools must perform fresh DB reads on each invocation (no stale cached slot lists in memory).
- Provide a booking tool that creates an appointment document in Azure DocumentDB (appointments collection) with explicit fields patientId, providerId, slotId, start, end, status ('booked'), and created/updated timestamps.
- Ensure booking is atomic: the booking tool must mark the chosen slot document’s status to 'booked' and create the appointment document inside a single MongoDB multi-document transaction (startSession/startTransaction + commitTransaction) against Azure DocumentDB so both changes succeed or both are rolled back.
- Implement rescheduling that updates the appointment and swaps slot statuses atomically: in the reschedule flow update the old slot to 'available', update or create the appointment for the new slot, and mark the new slot 'booked' inside a single transaction against Azure DocumentDB.
- Implement cancellation that sets appointment.status to 'cancelled' and sets the associated slot.status to 'available' atomically in one transaction against Azure DocumentDB.
- Use LangChain agent memory to persist conversational context (at minimum: last appointment id, patient identity, selected provider, and last referenced slot/time) and have the agent consult that memory so user utterances like "move it an hour later" resolve to the correct appointment without the user restating details.
- Wire the LangChain agent to call the DB tools via the LangChain tool invocation mechanism (i.e., agent decides to call the availability/booking/reschedule/cancel tools rather than performing DB calls inline in agent code).
- Detect and handle concurrent booking conflicts: booking/rescheduling code must verify transaction/update results (e.g., matched/modified counts or transaction commit status) and return a clear user-facing message when a slot became unavailable, offering next available slot alternatives queried from Azure DocumentDB.
- Include an end-to-end example or test script that demonstrates: a user books a slot, then says "move it an hour later", and the agent uses agent memory + the LangChain tools to perform the reschedule with the required atomic slot/appointment updates in Azure DocumentDB so a reviewer can reproduce and verify the full flow.

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
