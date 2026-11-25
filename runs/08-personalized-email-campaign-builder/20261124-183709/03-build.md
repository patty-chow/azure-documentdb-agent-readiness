# 3. Build report: 08-personalized-email-campaign-builder

**Status: partial**

Built a small Node.js sample that demonstrates fetching customer segment profiles from Azure DocumentDB, context-engineering a prompt, generating personalized email subject/body (via OpenAI or a deterministic fallback), and writing campaign documents back to the database. Project files, a seed script, a generator script, and README were created. npm install and the seed script executed successfully in this workspace. I could not fully verify reads/writes against the DocumentDB cluster using the documentdb MCP server during the run (the MCP server returned empty results and some MCP insert calls failed), and the generator run that depends on a segment lookup was not able to find the segment during verification runs. Details, evidence and next steps are below.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY and USE_OPENAI=1 to enable real OpenAI calls). 2) npm install 3) npm run seed   # upserts sample segments and creates basic indexes 4) npm run generate -- --segmentId=seg-1   # generates a campaign for segment 'seg-1' (uses deterministic fallback unless USE_OPENAI=1 and OPENAI_API_KEY are set).

## Verified by running

- npm install: 0 exit code, packages installed
- seed script (node src/seed.js): executed and printed 'Seeding complete. Segments upserted and indexes created.'

## Not verified

- DocumentDB data-plane verification of seeded documents with the documentdb MCP server: calls to documentdb_find_documents returned empty and documentdb_insert_documents failed. I could not confirm the seed documents were visible via the MCP server even though the seed script printed success.
- End-to-end generation and insertion using the generate script against the live cluster: a run of the generator (node src/generate.js --segmentId=seg-1) failed to find the segment in one attempt (logged 'Segment not found: seg-1') and earlier attempts timed out. This may be due to environment/connection-profile mismatch or transient connectivity/permission issues to the cluster in this run.
- Real OpenAI generation (chat completions) was not exercised because USE_OPENAI was intentionally disabled by default in the script to avoid network flakiness during automated verification; enabling real OpenAI calls requires setting USE_OPENAI=1 and OPENAI_API_KEY. I did not perform an actual OpenAI call in this run.

## Open issues

- documentdb MCP server visibility/compatibility: I observed inconsistent responses from the documentdb MCP server (empty results and failed inserts). This prevented programmatic verification using the MCP tools. Evidence: documentdb_find_documents returned no documents and documentdb_insert_documents returned an error when attempted.
- Generator cannot find seeded segment during verification: despite the seed script printing success, the generate script could not locate the segment in one run and earlier runs timed out. This suggests a cluster/connection mismatch, permissions issue, or a transient networking problem in the environment used for verification.
- LLM invocation is disabled by default to make automated verification deterministic: to use real OpenAI, set USE_OPENAI=1 and provide OPENAI_API_KEY in the environment. I intentionally defaulted to a deterministic fallback to avoid network-dependent flakiness during automated build/verification.
- If you want fully automated verification that includes vector search, embeddings and the LLM, you must provide valid OPENAI_API_KEY and set USE_OPENAI=1; also ensure the MCP server is correctly pointed at the same cluster or use the driver to inspect the same database used by the app.

## Files

- `package.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `src/client.js`
- `src/seed.js`
- `src/generate.js`
- `src/debug_list.js`

