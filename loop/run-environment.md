# Run environment

This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.

- A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable from this machine. Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks.
- Use the database named `{database}` for everything this sample creates. Do not read or change other databases on the cluster.
{mcp_line}- `python` and `pip` resolve to a virtual environment created for this run, so `pip install` works. Node.js 24 with npm and npx is available. Docker is installed, but no local DocumentDB gateway is running; build and verify against the live cluster instead of a local container.
- `az` is signed in and may read Azure resources. Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use.
- Verify against the live cluster: create the collections and indexes, load the sample data, run the queries the sample exists to show, and record in the build report what was actually executed and what was not.
