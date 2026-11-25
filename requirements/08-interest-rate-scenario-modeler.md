# Reference requirements: Interest rate scenario modeler

> Drafted by the model from the sample's title, description, concepts and starter prompt, then
> reviewed by a person. The builder never sees this file. The prompt reviewer predicts which
> lines the starter prompt will miss, and the auditor checks each line against what was built.
>
> One requirement per bullet, each something a reviewer can check in the code.

## What the starter prompt asks for

- Implement a Python LangChain agent (code must clearly instantiate and run a LangChain agent in Python).
- Implement a DocumentDB aggregation tool and register it as a LangChain Tool that issues an aggregation pipeline query against Azure DocumentDB.
- Ensure the grouping by rate type (explicitly "fixed" and "floating") and by maturity bucket is performed inside the DocumentDB aggregation pipeline (Mongo-style aggregation stages) returned by the DocumentDB aggregation tool, not only post-processed in Python.
- Define explicit maturity bucket boundaries in code or config (e.g., 0-1y, 1-3y, 3-5y, 5y+) and use those exact definitions in the aggregation pipeline so each position is assigned to a bucket by the DocumentDB query.
- Have the aggregation pipeline return numeric aggregates needed for NII calculations for each (rate type, maturity bucket) group: total balance, weighted-average interest rate, and count of positions.
- Include a small set of sample position documents and a script or instructions to insert them into Azure DocumentDB so the demo aggregation returns both fixed and floating positions across the defined maturity buckets.
- The LangChain agent must call the DocumentDB aggregation tool during its run and pass the tool output into the LLM context (i.e., tool outputs are consumed by the agent to drive the analysis).
- Use prompt engineering in the code: construct and pass a prompt that explicitly instructs the LLM to reason through Net Interest Income (NII) impact for the three scenarios—parallel shift, steepening, and inversion—and to base calculations on the aggregated data supplied by the DocumentDB aggregation tool.
- Require the agent to return a machine-readable structured scenario analysis report (JSON) containing, for each scenario and maturity bucket: scenario name, bucket name, rate type, baseline NII, shocked NII, absolute delta, percent delta, and a concise rationale sentence.
- Provide a runnable end-to-end demo (main entry point or script) that executes the LangChain agent, runs the DocumentDB aggregation tool against Azure DocumentDB, invokes the LLM with the engineered prompt, and outputs/saves the JSON scenario analysis report.

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
