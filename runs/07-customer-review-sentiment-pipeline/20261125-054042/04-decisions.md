# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| tool_result | 5 |
| prompt | 4 |
| operator | 2 |
| readiness_report | 2 |
| skill | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:46:10+00:00

## D002 (build): I chose Python 3.13 as the language/runtime for the sample.

- **Instead of:** Python 3.11; Python 3.13; Node.js
- **Because:** The run environment already has Python 3.13 available; using the available interpreter avoids extra setup and matches the developer machine.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 on PATH" in run environment.
- **When:** 2026-11-25T13:48:14+00:00

## D003 (build): I chose Beanie ODM with Motor async driver for model convenience and alignment with the prompt.

- **Instead of:** Use raw Motor/PyMongo without ODM; Use Beanie ODM with Motor; Use Beanie with PyMongo AsyncMongoClient
- **Because:** The prompt explicitly requests Beanie; Motor is the traditional async driver used with Beanie in many examples. I will reuse Beanie for document models and Motor client for the connection.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: "build an async Python pipeline using Beanie ODM".
- **When:** 2026-11-25T13:48:17+00:00

## D004 (build): I chose to pin conservative versions: beanie==1.13.0, motor==3.1.0, pydantic==1.10.12, openai==0.27.8, python-dotenv==1.0.0.

- **Instead of:** Pin latest known versions automatically; Pin specific versions suggested in prompt review; Leave versions unpinned
- **Because:** Pinning explicit versions improves reproducibility for the sample; I selected conservative pins suggested by the prompt review. If these prove incompatible, that's recorded in the build report.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review suggested example pins ("e.g. beanie==1.13.0, motor==3.1.0").
- **When:** 2026-11-25T13:48:20+00:00

## D005 (build): I chose to use the public OpenAI API with OPENAI_API_KEY environment variable.

- **Instead of:** Use Azure OpenAI (AZURE_OPENAI_* env vars); Use public OpenAI (OPENAI_API_KEY)
- **Because:** Public OpenAI is broadly available and simple to demonstrate; the sample will document this requirement in .env.example. If the user prefers Azure OpenAI they can adapt the code later.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report 'information_gaps' notes the choice is not specified and builder must choose provider.
- **When:** 2026-11-25T13:48:24+00:00

## D006 (build): I chose gpt-3.5-turbo as the model for classification and theme extraction.

- **Instead of:** gpt-4; gpt-3.5-turbo; gpt-4o-mini
- **Because:** Lower cost vs gpt-4 for a sample dataset; demonstrates pattern without incurring high usage. The code will accept a MODEL env var to change this.
- **Reason came from:** `model_default`
- **Evidence:** No model mandated in prompt or skills; gpt-3.5-turbo is cost-effective and commonly available.
- **When:** 2026-11-25T13:48:27+00:00

## D007 (build): I chose a bounded concurrency semaphore of 8 for OpenAI calls.

- **Instead of:** No concurrency limit (unbounded); Bounded concurrency semaphore 4; Bounded concurrency semaphore 8; Batch calls
- **Because:** Small dataset and typical rate limits — 8 concurrent requests balances speed and risk of hitting rate limits; it's configurable in code.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Batch sizing and concurrency for OpenAI calls' is unspecified; choose reasonable default.
- **When:** 2026-11-25T13:48:30+00:00

## D008 (build): I chose to create a single-field index on product_id and a compound index on (product_id, sentiment_score) to support aggregation and filtering by product and sentiment.

- **Instead of:** Create only _id index; Add indexes on product_id and created_at; Add index on product_id and a compound index on (product_id, sentiment_score)
- **Because:** Aggregation grouped by product and sentiment will run efficiently with product_id indexed; the compound index supports queries that filter or sort by sentiment within a product. Keep index budget small for sample dataset.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill: 'prefer one compound over many singles' and 'Query-pattern → index-shape cookbook'.
- **When:** 2026-11-25T13:48:36+00:00

## D009 (build): I chose to adjust motor to motor==3.1.2 because pip reported 3.1.0 is not available in the environment.

- **Instead of:** Keep motor==3.1.0 and fail; Adjust motor pin to an available 3.1.x release
- **Because:** Use a nearby available patch release (3.1.2) to satisfy compatibility while keeping close to the originally chosen major/minor version.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: "No matching distribution found for motor==3.1.0" during install attempt.
- **When:** 2026-11-25T13:49:29+00:00

## D010 (build): I chose to remove aiohttp from requirements to avoid building a C-extension wheel that fails on Python 3.13 in this environment.

- **Instead of:** Keep aiohttp and attempt to build (may fail); Remove aiohttp from requirements to avoid native build on Python 3.13
- **Because:** aiohttp is not required by the sample directly; removing it avoids the failing build. The OpenAI client and other deps function without an explicit aiohttp pin for this sample.
- **Reason came from:** `tool_result`
- **Evidence:** pip failure: building wheel for aiohttp failed with C compile errors on Python 3.13.
- **When:** 2026-11-25T13:49:42+00:00

## D011 (build): I chose to add small pymongo-based helper scripts for seeding and index creation for verification, because Beanie/Motor imports failed in this Python 3.13 environment (ImportError during runtime).

- **Instead of:** Force-install other motor/pymongo versions and retry; Use synchronous pymongo-only scripts for seeding/indexing to avoid Beanie/Motor import issues during verification
- **Because:** Using pymongo directly avoids the motor/beanie import path for quick verification steps and keeps the Beanie-based code in the repo for users; document this in the build report.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor' when importing motor/beanie during seed run.
- **When:** 2026-11-25T13:50:12+00:00

## D012 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:52:01+00:00

## D013 (build): I chose Python (async) for the sample and targeted a modern 3.11+ runtime but wrote code compatible with the available Python on the machine (3.13 as reported).

- **Instead of:** Python 3.11; Python 3.13
- **Because:** The prompt requested an async Python pipeline; the environment already has Python and is compatible with 3.11+; code will be compatible across 3.11–3.13.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use Python 3.11 (current LTS / modern default).' Readiness report: 'Python 3.13.13 on PATH'
- **When:** 2026-11-25T13:52:19+00:00

## D014 (build): I chose Beanie ODM with Motor async driver and pinned compatible versions in requirements.txt (beanie==1.19.1, motor==3.1.1, pydantic==1.10.12).

- **Instead of:** Beanie latest stable with Motor; Use raw Motor or PyMongo without Beanie ODM
- **Because:** Beanie fits the prompt ('Using Beanie ODM'); Motor is required for async MongoDB access; pinning versions increases reproducibility.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Beanie (latest stable compatible) with Motor async driver (motor >= 3.x)'; Beanie provides ODM convenience for document models and indexing.
- **When:** 2026-11-25T13:52:22+00:00

## D015 (build): I chose the public OpenAI API (OPENAI_API_KEY) as the default provider for this sample, but implemented a mock/local fallback when the key is not set to avoid incurring external API calls during verification.

- **Instead of:** Use Azure OpenAI provider (AZURE_OPENAI_* env vars); Use public OpenAI API (OPENAI_API_KEY)
- **Because:** Public OpenAI is widely available and simpler for sample code; providing a mock mode avoids requiring the key for verification and prevents accidental costs.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'The builder must choose (OPENAI_API_KEY vs AZURE_OPENAI_ENDPOINT/KEY)'; Assumption from prompt review: 'Use OPENAI_API_KEY'.
- **When:** 2026-11-25T13:52:26+00:00

## D016 (build): I chose bounded concurrency for OpenAI calls using asyncio.Semaphore with a default concurrency of 5.

- **Instead of:** Call OpenAI for each review with unbounded concurrency; Call OpenAI with bounded concurrency (semaphore)
- **Because:** Limits rate of outbound LLM requests to be safe and avoid exhausting local resources or API rate limits.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'The call is awaited per review and run concurrently with a bounded semaphore.' No skill gave a specific concurrency so pick a conservative default.
- **When:** 2026-11-25T13:52:29+00:00

## D017 (build): I chose a small synthetic sample dataset with 100 records (data/sample_reviews.json) and an idempotent seed script.

- **Instead of:** Create a large synthetic dataset (~1000s); Create a small synthetic dataset (~100 records)
- **Because:** Keeps costs and run time small while providing enough data to exercise aggregation and indexing.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Include a small synthetic sample file (~50–200 records)'.
- **When:** 2026-11-25T13:52:32+00:00

## D018 (build): I chose to declare indexes in the Beanie model (Settings.indexes) for product_id and a compound index on product_id + sentiment_score (descending), and verify them with the documentdb MCP server.

- **Instead of:** Create indexes via Beanie model Settings and let Beanie create them; Manually create indexes using the documentdb MCP server or Mongo commands
- **Because:** Beanie keeps index definitions with code and can create them at init; MCP server verification provides live confirmation on the target cluster.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill
- **When:** 2026-11-25T13:52:39+00:00

## D019 (build): I chose to pin beanie==1.13.0 and motor==3.1.2 to avoid runtime ImportError from pymongo internals and match a known-compatible stack on this runner.

- **Instead of:** Keep beanie==1.19.1 and fix pymongo mismatch; Downgrade to beanie==1.13.0 and motor==3.1.2 which were present and compatible
- **Because:** Restore the previously-installed, compatible beanie/motor versions to avoid pymongo API incompatibilities observed at runtime.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor' when importing beanie; initial install replaced existing beanie 1.13.0 with 1.19.1 and motor 3.1.1.
- **When:** 2026-11-25T13:54:25+00:00

## D020 (build): I chose to pin pymongo==4.6.0 to resolve ImportError for internal symbol _QUERY_OPTIONS used by motor/beanie on this runner.

- **Instead of:** Keep current pymongo (4.20.1) and debug deeper; Pin pymongo to an older 4.x release (e.g. 4.6.0) known to expose internal symbols motor expects
- **Because:** Pinning to a compatible pymongo 4.x release is the fastest way to resolve motor/beanie import errors without reworking code.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor' when importing motor/core.py; indicates an API/internal change in pymongo 4.20.1.
- **When:** 2026-11-25T13:54:43+00:00
