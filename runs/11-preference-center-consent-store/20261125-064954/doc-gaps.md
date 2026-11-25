# Documentation and tooling gaps: 11-preference-center-consent-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Pinned dependency guidance for samples

- **What was missing:** No public doc (search not available in this run) was included that instructs gallery samples to pin dependency versions or provides a canonical set of tested package versions for Beanie/Motor/Pydantic used in DocumentDB samples.
- **Where the agent looked:** Local repository files (. / app/requirements.txt) and no external documentation server was reachable from this environment.
- **Effect on this build:** The builder left requirements.txt unpinned (decision D003). This can cause version incompatibilities for future consumers and may force builders to debug runtime incompatibilities (observed beanie/motor compatibility issues in this run).
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule: 'All gallery Python samples must pin package versions in requirements.txt to the tested versions used during sample build. Provide a short table of pinned versions for fastapi, beanie, motor, pydantic and uvicorn. Example requirements.txt excerpt and a note explaining how to update pins for future releases.'

## [high] Connection options and TLS recommendation

- **What was missing:** Authoritative guidance and copyable connection-string examples documenting canonical TLS/SSL parameters, certificate verification options, and sensible pool/timeouts for AsyncIOMotorClient against Azure DocumentDB were not available to the agent in this run.
- **Where the agent looked:** Local repo files and the run-time readiness notes; external documentation search was not available in this environment.
- **Effect on this build:** The sample uses the DOCUMENTDB_URI env var as-is (good), but no explicit guidance or example is given for TLS/verification or recommended connection options. This leaves users unsure how to configure secure and robust driver settings.
- **Suggested fix (learn_doc):** Publish a small 'Connection string and driver options' page in the DocumentDB agent kit / product docs that shows sanitized examples of DOCUMENTDB_URI (SRV and non-SRV forms), TLS/ssl parameters, recommended maxPoolSize and timeouts for a small sample app, and code snippets showing AsyncIOMotorClient creation with explicit options. Include a short note on verifying certificates vs. dev-only allow-invalid settings.

## [high] Microsoft Entra ID (AAD) authentication flow for drivers

- **What was missing:** No public snippet was discoverable in this run describing whether and how the MongoDB-compatible driver can authenticate using AAD tokens (if supported), or a clear statement that AAD-based auth is unsupported for this engine/version.
- **Where the agent looked:** Local repository and run-time readiness notes; external docs were not reachable.
- **Effect on this build:** The builder used DOCUMENTDB_URI env var; without AAD documentation, future contributors might attempt unsupported flows or miss an opportunity to support AAD where available.
- **Suggested fix (learn_doc):** A product doc page 'Authentication options' that lists supported auth methods (SCRAM/username-password, X.509, AAD if supported), with a code example showing how to obtain an AAD token and present it to the driver (or explicit statement that AAD is unsupported), and recommended fallback patterns for samples.

## [medium] Append-only history operational guidance

- **What was missing:** Public guidance specific to Azure DocumentDB on how to handle append-only history arrays (e.g., when to cap in-document arrays vs. use a separate history collection, and the performance/size tradeoffs).
- **Where the agent looked:** Repository and prior-knowledge list; external docs unreachable.
- **Effect on this build:** The sample implements an unbounded history array (satisfies the prompt), but without published guidance implementers may choose an approach that later causes growth/performance issues at scale.
- **Suggested fix (learn_doc):** A short guidance page 'Modeling audit history' with (a) recommended patterns (capped array size, shadow history collection, periodic archival), (b) sample code for each pattern (Beanie + motor), (c) TTL/retention implications if expiring audit events, and (d) when to prefer each approach.

## [medium] Retryable writes and idempotency guidance

- **What was missing:** Explicit, discoverable guidance on enabling driver retryable writes and on designing idempotent write endpoints (idempotency keys, deterministic upsert ids) for DocumentDB.
- **Where the agent looked:** Local repo and prior-beliefs; external docs unreachable.
- **Effect on this build:** The sample does not implement explicit retry or idempotency beyond unique index avoidance of duplicates; without documentation, authors may enable retries without making operations idempotent, risking duplicate history entries.
- **Suggested fix (learn_doc):** A 'Retries and idempotency' guidance page with recommended driver flags for retryable writes, example client-side backoff/retry wrapper, and a short pattern for idempotent endpoints (idempotency key header handling or deterministic event ids in upserts).

## [medium] Provisioning / management-plane snippets

- **What was missing:** Authoritative management-plane snippets (ARM/Bicep/Terraform and az CLI examples) for provisioning DocumentDB database accounts for this exact product were not available to the agent in this run.
- **Where the agent looked:** Run-time readiness notes; external docs not accessible here.
- **Effect on this build:** The sample does not include infra-as-code; contributors cannot rely on local guidance to reproduce the exact cloud resource types or required CLI commands.
- **Suggested fix (mcp_tool_or_description):** Ship a small infra snippet (ARM/Bicep and a short az CLI example) in the agent kit or sample 'infra' folder that provisions a minimal DocumentDB account and the sample database, plus a note about cost/region defaults and cleanup steps.

