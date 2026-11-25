DocumentDB Appointment Scheduling Assistant (Node.js)

This sample demonstrates a Node.js LangChain-based appointment scheduling assistant that uses Azure DocumentDB (MongoDB wire protocol) for storing provider slots and appointments. It includes:

- A small Express server exposing a /chat endpoint that forwards conversational messages to a LangChain-based agent with in-memory conversation memory.
- Tools for querying available slots, creating appointments atomically, rescheduling and cancelling (implemented with MongoDB transactions/conditional updates).
- A seed script that idempotently creates sample slots and an appointment.

Prerequisites

- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in your environment (see .env.example). Do NOT commit secrets.
- An OpenAI API key (OPENAI_API_KEY) for the sample agent LLM.

Files

- src/db.js - MongoDB singleton connector
- src/seed.js - Idempotent seed script (creates 'slots' and 'appointments' collections, indexes, sample docs)
- src/store.js - Domain operations: findAvailableSlots, createAppointmentAtomic, rescheduleAppointmentAtomic, cancelAppointment
- src/agent.js - Minimal LangChain-based agent using ChatOpenAI + BufferMemory and a small toolset
- src/server.js - Express HTTP server with /chat endpoint
- src/demo_seed_verify.js - One-shot script to verify data-plane behaviour (find slots, book, reschedule, cancel)

Setup

1. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY. DATABASE_NAME defaults to sample_healthcare_05.

2. Install dependencies:

   npm install

3. Seed the database (idempotent):

   npm run seed

4. Verify basic data-plane operations (find slots, create appointment, reschedule, cancel):

   npm test

5. Start the server (optional):

   npm start

Then POST to http://localhost:3000/chat with JSON { "userId": "patient_123", "message": "I want to book an appointment with provider_1 tomorrow at 10am" }

Notes and limitations

- The agent uses an in-memory BufferMemory, which is ephemeral. For production persist memory in a durable store.
- The LangChain agent in this sample uses a simple JSON-call convention: the model is instructed to return a JSON object indicating which tool to call. This keeps the sample code small and focused on DB interactions; a fuller production agent would use LangChain's AgentExecutor, richer tool schemas, and more robust parsing.
- The seed and verification scripts run against the provided cluster and will create/update documents in the specified database. Do not use on production clusters.

Security

- Never check secrets into source control. Use environment variables or a secrets store.

License

MIT
