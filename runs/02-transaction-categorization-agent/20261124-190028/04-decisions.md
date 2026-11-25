# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| operator | 1 |
| model_default | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:28:57+00:00

## D002 (build): I chose Node.js (v24) with Express and LangChain JS for the agent.

- **Instead of:** Python/Flask; Node.js/Express
- **Because:** The prompt explicitly requests Node.js + LangChain; Express provides a simple HTTP surface to expose endpoints.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain agent' (sample_prompt)
- **When:** 2026-11-25T06:29:16+00:00

## D003 (build): I chose the official mongodb Node.js driver at mongodb@5.x.

- **Instead of:** mongodb@4.x; mongodb@5.x; mongodb@6.x
- **Because:** Driver 5.x is commonly used with MongoDB 7 wire protocol and aligns with the prompt-review assumption and documentdb-driver guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official mongodb Node.js driver (npm package "mongodb"), current stable release compatible with MongoDB 7.0 (e.g., mongodb@5.x)'.
- **When:** 2026-11-25T06:29:19+00:00

## D004 (build): I chose OpenAI (environment variable OPENAI_API_KEY) as the LLM provider for LangChain.

- **Instead of:** Use OpenAI (OPENAI_API_KEY); Use Azure OpenAI (AZURE_OPENAI_KEY); Use Anthropic or other model
- **Because:** OpenAI is widely available, LangChain has direct adapters, and it's simplest for the sample. The README will document required env vars.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM/provider selection and env vars missing' — builder must decide; OpenAI is a common default and supported by LangChain.
- **When:** 2026-11-25T06:29:25+00:00

## D005 (build): I chose a compound index on { date: 1, category: 1 } for the transactions collection.

- **Instead of:** No indexes; Single-field index on date and category separately; Compound index on {date:1, category:1}
- **Because:** Aggregation groups by month (derived from date) and category; this compound index aligns with common query pattern and helps the pipeline; it follows ESR guidance to create compound indexes for common query shapes.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Create an index on { date: 1, category: 1 }' and documentdb-indexing guidance preferring compound indexes for aggregation/grouping patterns.
- **When:** 2026-11-25T06:29:39+00:00
