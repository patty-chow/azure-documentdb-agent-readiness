Azure DocumentDB Outreach Orchestration Sample

What this shows

- A minimal Node.js orchestration pipeline that listens to Azure DocumentDB (MongoDB wire) change streams for qualifying customer events (cart_abandon, contract_renewal, birthday).
- A copy agent that uses an LLM (via LangChain/OpenAI) to generate a personalized outreach message.
- A send agent that (by default) runs in sandbox mode and records outcomes to the outreach_logs collection.
- CLI scripts to seed sample data, run a one-shot processing job, start the long-running listener, and a small REST API to query outreach logs.

Prerequisites

- Node.js 24+, npm
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in environment.
- An OpenAI API key in OPENAI_API_KEY (or configure another LangChain provider).
- The sample uses the database named 'sample_customer_360_19'.

Setup

1. Copy .env.example to .env and fill in secrets (do NOT commit .env).
2. npm install
3. npm run seed

Run

- One-shot run to process existing qualifying events: npm run run-once
- Start the long-running listener: npm start
- Start the REST server to view logs: npm run server (GET /logs)

Cleanup

- Remove the created collections from the sample database manually or via your UI.

Notes and safety

- By default SANDBOX_SEND=true in .env.example. No real emails/SMS will be sent. To enable real sends, replace the sendAgent implementation with your provider and set SANDBOX_SEND=false.
- Secrets must be provided via environment variables. Never check real keys into source control.

Development

- Simple test runner included: npm test (runs basic smoke checks that can be executed without external providers by setting OPENAI_API_KEY to a valid key).

Contact

This sample is provided as-is for educational purposes.
