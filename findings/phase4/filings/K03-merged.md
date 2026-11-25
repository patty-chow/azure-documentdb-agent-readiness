---
id: K03
title: "security and connection skills: Microsoft Entra ID (MONGODB-OIDC) data-plane auth with runnable per-driver examples, and a rule for sensitive data in AI/LLM applications"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 99
member_drafts:
  - 016-believes-entra-id-is-not-supported-for-data-plane-auth-only-.md
  - 014-believes-authentication-is-account-key-username-password-scr.md
  - 017-believes-an-entra-access-token-is-passed-via-the-wrong-mecha.md
  - 018-unaware-that-entra-id-is-an-opt-in-cluster-setting-authconfi.md
  - 041-believes-vcore-lacks-or-restricts-platform-features-it-suppo.md
  - 101-security-and-production-hardening-guidance-absent-single-adm.md
  - 122-security-and-compliance-practices-for-ai-applications-on-azu.md
merged_from:
  - K03
  - K35
open_questions: 3
---

# security and connection skills: Microsoft Entra ID (MONGODB-OIDC) data-plane auth with runnable per-driver examples, and a rule for sensitive data in AI/LLM applications

This PR combines two filings that both add rules under `skills/security/` and edit `skills/security/SKILL.md`, and both deal with redaction: K03 (Entra ID data-plane auth, plus a connection-error redaction rule and production-hardening helpers) and K35 (PHI/PII and secrets in AI/LLM data flows). If the reviewer prefers K03 as a stand-alone cross-cutting auth PR, split out section 6 below (`security-ai-sensitive-data.md`) and the K35 lines in section 3 as their own PR.

## What happens today

**Authentication guidance (K03).**

- An agent that writes connection code loads `skills/connection/SKILL.md`. Its whole "Authentication" section is two bullets: "Default mechanism: `SCRAM-SHA-256`" and "Credentials are managed through the Azure portal". It does not mention Microsoft Entra ID, and `skills/driver/SKILL.md` does not mention auth at all.
- The only application-side Entra guidance is `skills/security/security-entra-rbac.md` (priority MEDIUM), reachable only if the agent opens the security skill and follows the sub-link. Its "Correct" block cannot authenticate as written:
  - It has `authMechanism: "MONGODB-OIDC", // or the current documented mechanism`, with `// credentialProvider: Azure Managed Identity` left as a comment, and tells the reader to "verify current driver support/spec in the official docs".
  - It sets no `authMechanismProperties`, so there is no `OIDC_CALLBACK` and no `TOKEN_RESOURCE`.
  - It never says that Entra has to be enabled on the cluster (`authConfig.allowedModes`) or that each identity has to be registered as a cluster user.
  - Its least-privilege SCRAM example grants `{ role: "readWrite", db: "orders" }`, which is not one of the roles Learn lists for secondary users.
- `skills/azure-deployment/SKILL.md` (near line 311) has only "Entra RBAC / CMK / diagnostic settings. See `documentdb-security`". The Bicep and Terraform references never set `authConfig`.
- `skills/mcp-setup/SKILL.md` uses `authMode: "entra"` but never says how to tell whether the cluster allows it. The kit README calls Entra/OIDC the *recommended* mode for the MCP server, yet the skills never tell application code the same thing.
- The Learn page [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control) already documents the enable command, admin and non-admin registration, the token scope, and Python, TypeScript and C# callbacks. The gap is in the kit.

**Sensitive data and redaction (K03 draft 101, K35).**

- `skills/security/SKILL.md` lists four rules: TLS, Private Endpoint, Entra RBAC and CMK. None covers redacting connection URIs or tokens from logged errors, or what a generated AI application does with sensitive data on its way to and from the model: prompts, logs, agent memory and per-user authorization.
- The kit's two related safety sections govern the agent's own behaviour, not the code it generates, and the security skill links to neither:
  - `skills/natural-language-querying/SKILL.md` ("Safety: Handling Sensitive Data in Sampled Documents") lists field names and value patterns for redacting secrets and PII in documents the agent itself samples.
  - `skills/mcp-setup/SKILL.md` ("Safety: never receive credentials in chat") keeps the connection string out of chat, files and generated examples.
- The Learn page [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security) covers network, identity, TLS, encryption at rest, backup and audit logs, but says nothing about LLM data flows or client-side field-level encryption.

## Why it matters

We ran one agent-readiness experiment: 100 Azure DocumentDB sample prompts, each built by gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers. All counts below come from that single run and will move on a re-run.

- **Entra ID auth (K03): 99 distinct samples.**
  - **98 of 100 samples** answered the cold-quiz question "Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID?" wrong or partly wrong (recounted from each run's `02-readiness.json`). The wrong answers fell into three groups:
    - **"Control-plane only" (67 samples, draft 016).** Entra is control-plane only and the wire endpoint takes SCRAM only; this is the Azure Cosmos DB for MongoDB (RU) prior.
    - **Invented mechanisms (15 samples, draft 017).** The token passed as a SCRAM password, `MONGODB-AZUREAD`, `PLAIN` with `$external`, `OAUTHBEARER`/`GSSAPI`, X.509.
    - **Opt-in step missing (17 samples, draft 018).** 15 said Entra is unavailable on the wire protocol or assumed it works without enabling anything; 2 described the Cosmos DB for NoSQL model (account keys, or Azure RBAC role assignments on the account).
    - The three groups sum to 99 because one sample falls in two of them; they cover 98 distinct samples.
  - A related cold question about the connection-string format got the auth part wrong in **35 samples** (36 findings, draft 014), using the `:10255` "the password is the account key" form.
  - **Effect on the builds:** most builds shipped a single admin SCRAM `DOCUMENTDB_URI`; a recount of app source files finds `MONGODB-OIDC` in only **23 of 100** builds, and the audit stage repeatedly flagged that Entra was not shown or not explained. In `14-customer-complaint-classifier` the builder skipped OIDC to "avoid complex OIDC setup"; the harness-supplied URI was the main reason, but the kit offered no cheap working alternative.
  - **1 further sample** (`03-medication-interaction-checker`, draft 101): the practice audit flagged a SCRAM-only app with no Entra path, no TLS guard and unredacted connection errors.
- **Sensitive data in AI/LLM apps (K35): 15 samples** (16 findings, draft 122). The auditor marked these practices "prior knowledge only" because it found no Microsoft source to cite:
  - redact PHI/PII (patient ids, names, account numbers, clinical text) from logs and error traces;
  - minimise or redact PII before sending text to an LLM; for PHI, use an endpoint covered by the organisation's agreements or de-identify locally first;
  - never put a connection string or key in a prompt or tool argument; the model reaches the database only through parameterized tools;
  - persist only identifiers in agent memory, not full PII-bearing context;
  - check in the app layer that the caller may read a given patient or tenant before querying, instead of relying on a query filter alone.

  Examples: a clinical de-identification build added an OpenAI run mode for clinical notes with no compliance guardrail; a care-coordination audit recommended client-side field-level encryption (CSFLE) for PHI and found no source saying whether DocumentDB supports it; a dynamic-pricing build kept secrets out of prompts but had nothing to cite. Graders scored these checks "not assessable", so whether a build gets them right depends on what the model happens to know.
- **Combined: 99 distinct samples.** All 15 K35 samples are already among K03's 99, so the union stays at 99 (one run). The one sample outside K03, `14-loan-origination-workflow-orchestration`, answered the auth question correctly and has no K35 finding.

## Proposed change

Each kit file appears once below, with all of its edits. This PR does **not** cover:

- Host-suffix fixes (`.mongocluster.documentdb.azure.com` → `.mongocluster.cosmos.azure.com`) and the connection-string `retryWrites` line: K01.
- Change-stream and transaction rules: K04 and K15.
- Generic LLM endpoint hygiene (rate limits, feature flags, fallbacks): it came up in a few samples but has no DocumentDB angle.

### 1. `skills/connection/SKILL.md`

**a. Replace "### Authentication" with:**

````markdown
### Authentication modes

Azure DocumentDB accepts two data-plane modes; the cluster's `authConfig.allowedModes` decides which are on (`NativeAuth` only, by default).

| | Native user | Microsoft Entra ID |
|---|---|---|
| `authMechanism` | `SCRAM-SHA-256` | `MONGODB-OIDC` |
| Credential | user + password | token from `DefaultAzureCredential` (managed identity, workload identity, `az login`) for scope `https://ossrdbms-aad.database.windows.net/.default`; no password |
| Prerequisite | user exists on the cluster | `MicrosoftEntraID` in `allowedModes` and the principal registered as a cluster user (see `security-entra-rbac`) |
| Use for | local container (port 10260), tools without OIDC | code running in Azure / production |

There are no account keys. Never pass an Entra token as a password.

**Python (pymongo + azure-identity; same kwargs for `AsyncMongoClient`):**
```python
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential): self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        return OIDCCallbackResult(access_token=self.credential.get_token(SCOPE).token)

# HOST is the hostname from the connection string the portal or CLI returns
# (<cluster>.mongocluster.cosmos.azure.com); never build it from the cluster name.
client = MongoClient(
    f"mongodb+srv://{HOST}/",
    tls=True, retryWrites=False, maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
)
```

**Node.js (mongodb + @azure/identity):**
```javascript
const { MongoClient } = require("mongodb");
const { DefaultAzureCredential } = require("@azure/identity");
const SCOPE = "https://ossrdbms-aad.database.windows.net/.default";
const credential = new DefaultAzureCredential();
// HOST: hostname from the portal/CLI connection string (<cluster>.mongocluster.cosmos.azure.com)
const client = new MongoClient(`mongodb+srv://${HOST}/`, {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const t = await credential.getToken(SCOPE);
      // expiresOnTimestamp is in milliseconds
      return { accessToken: t.token, expiresInSeconds: Math.max(0, Math.floor((t.expiresOnTimestamp - Date.now()) / 1000)) };
    },
    // Required: the Node driver checks ALLOWED_HOSTS for every custom OIDC callback and its
    // default list has no Azure domain. Checked against the SRV-resolved node hosts, so it must
    // be a wildcard; keep it on the service domain, never "*".
    ALLOWED_HOSTS: ["*.mongocluster.cosmos.azure.com"],
  },
});
```

Mongoose: pass the same options to `mongoose.connect(uri, options)`; they go through to the driver. PyMongo does not check `ALLOWED_HOSTS` for machine callbacks, so the Python snippet needs none.

Driver floors for `MONGODB-OIDC`: PyMongo 4.7, Node `mongodb` 6.7.0, Java 5.1, .NET `MongoDB.Driver` 2.25 (3.x is current). `AsyncMongoClient` exists from PyMongo 4.9 (beta) and is GA from 4.13.

**Fall back to SCRAM-SHA-256 only when** the cluster does not have Entra enabled, the runtime has no Azure identity (for example a CI machine outside Azure without `az login`), or the client is a third-party tool that cannot run an OIDC callback. Then use a least-privilege secondary user created by an admin, never the built-in admin. `DefaultAzureCredential` covers `az login` locally and managed identity in Azure, so the same Entra code runs in both places.

Host: copy the connection string from the portal (Cluster > Settings > Connection strings) or `az documentdb mongocluster list-connection-strings`. On a single cluster the Self string (`<cluster>.mongocluster.cosmos.azure.com`) and the Global read-write string (`<cluster>.global.mongocluster.cosmos.azure.com`) are interchangeable. If the cluster has or may get a cross-region replica, use the Global read-write string for writes so that a promotion needs no code change; the Self string of the old primary becomes read-only after promotion, and replica clusters expose only a Self string. Never construct the host from the cluster name. mongosh/Compass on an Azure host with a managed identity:
`mongodb+srv://<client-id>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000&authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net`

Do not tell users Entra ID is "control-plane only" or unsupported on the MongoDB wire protocol; that was Azure Cosmos DB for MongoDB (RU), not Azure DocumentDB. Cluster setup, user registration, other drivers: `documentdb-security` › security-entra-rbac. Full walkthrough: https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control
````

**b. TLS guard.** Add a small `require_secure_uri(uri)` helper (Python, with a Node equivalent). It raises unless the URI has `tls=true` (or `ssl=true`), and it refuses `tlsAllowInvalidCertificates=true` or `tlsInsecure=true` outside local development.

**c. "When Creating Code".** Add one line: every generated app that reads `DOCUMENTDB_URI` calls the TLS guard, uses the redacting logger from `security-redact-logs`, and includes the README block from `security-sample-readme-production-notes`.

**d. "Related skills".** Add the section (there is none today) naming `documentdb-security` › security-entra-rbac.

### 2. `skills/driver/SKILL.md`

After the singleton rule, add: "Authentication: SCRAM-SHA-256 or Microsoft Entra ID (`MONGODB-OIDC`). See `documentdb-connection` › Authentication modes."

### 3. `skills/security/SKILL.md`

- **Front-matter `description`:** insert `, and handling PHI/PII in AI/LLM applications built on DocumentDB` right after "customer-managed keys (CMK) for encryption at rest" (before the period that precedes "Use when"), and add `building AI/LLM apps that handle PHI or PII` to its "Use when" list, so the skill triggers for these prompts.
- **Update the security-entra-rbac index line** to: "Enable Entra on the cluster, register principals, connect with MONGODB-OIDC; least-privilege secondary users".
- **Add to `## Rules`** (the two K03 rules are listed by name in the filing; the one-line descriptions here are derived from their content):

  ```markdown
  - [security-redact-logs](security-redact-logs.md) — Never log connection URIs, tokens or raw errors/documents; log name, code and a redacted message.
  - [security-sample-readme-production-notes](security-sample-readme-production-notes.md) — README block every generated sample ships: auth, secrets and production notes.
  - [security-ai-sensitive-data](security-ai-sensitive-data.md) — Keep secrets out of prompts; redact PHI/PII from LLM calls, logs and agent memory; authorize per patient/tenant before querying.
  ```

### 4. `skills/security/security-entra-rbac.md`

- **Add before "Incorrect": "How authorization works on Azure DocumentDB".**
  - **There are no account keys.** Native auth is a SCRAM user + password. Cosmos DB "primary key" and "resource token" auth do not exist here.
  - **Entra is opt-in per cluster.** Enable it with `az documentdb mongocluster update --name <cluster> --resource-group <rg> --auth-allowed-modes NativeAuth MicrosoftEntraID`. Keep `NativeAuth` until an Entra principal has connected. Check the result with `az documentdb mongocluster show ... --query properties.authConfig`.
  - **Enabling the mode grants nobody access.** Azure role assignments on the `mongoClusters` resource control management only. Data access comes from MongoDB roles on a principal registered inside the cluster.
  - **Administrator (`root` on `admin`).** Register with `az documentdb mongocluster microsoft-entra-user assign --cluster-name <cluster> --resource-group <rg> --object-id <object-id> --type <User|ServicePrincipal> --role db=admin role=root` (an idempotent upsert; the `documentdb` extension needs Azure CLI 2.75.0+), or with the ARM/Bicep `Microsoft.DocumentDB/mongoClusters/users` resource (`identityProvider.type: MicrosoftEntraID`, `principalType: user | servicePrincipal`; the resource name is the principal's object ID), or with Terraform `azurerm_mongo_cluster_user` (azurerm >= 4.55.0). `--type` accepts exactly `User` and `ServicePrincipal`; a service principal or managed identity takes `ServicePrincipal` with its **object ID** (`principalId` from `az identity show`, or the owning resource's `identity.principalId` for a system-assigned identity), never the application/client ID. The ARM endpoint supports administrative registration only.
  - **Nonadministrative (least privilege).** An Entra admin runs `createUser` with the principal's **object ID**, not its client ID:
    - roles `clusterAdmin` + `readWriteAnyDatabase` together (they cannot be assigned separately; `clusterAdmin` in this pair grants no user-management rights), or `readAnyDatabase` alone for read-only. These are the only accepted built-in combinations; anything else fails with "Roles specified are invalid. Only readAnyDatabase or readWriteAnyDatabase+clusterAdmin are allowed built-in roles."
    - `customData: { IdentityProvider: { type: "MicrosoftEntraID", properties: { principalType: "servicePrincipal" } } }`.

    Verify with `db.getSiblingDB("admin").runCommand({ usersInfo: 1 })` (or, as the identity itself, `connectionStatus` with `showPrivileges: true`). ARM user listings do not show these database-only users.
- **Add a second "Incorrect" block** listing the mechanisms that fail:
  - an Entra token passed as a SCRAM password;
  - `MONGODB-AZUREAD`;
  - `PLAIN`, `GSSAPI` or `MONGODB-X509` with `authSource=$external`;
  - raw `OAUTHBEARER`;
  - an Atlas human-flow OIDC configuration copied unchanged (no callback and no `TOKEN_RESOURCE` for the `ossrdbms-aad` resource);
  - a Node `MONGODB-OIDC` client with a custom callback and no `ALLOWED_HOSTS`: the driver's default list has no Azure domain, so every connection fails with `MongoInvalidArgumentError: Host ... is not valid for OIDC authentication with ALLOWED_HOSTS of ...`.

  Note that `$external` itself is correct for MONGODB-OIDC; drivers set it by default.
- **Replace the "Correct" block** with:
  - the prerequisites above;
  - "Python and Node: see `documentdb-connection` › Authentication modes";
  - the .NET form from Learn: `MongoCredential.CreateOidcCredential(new AzureIdentityTokenHandler(new DefaultAzureCredential(), tenantId))`, where the handler implements `IOidcCallback` for the same scope;
  - the Java form from Learn's [Build a Java console app](https://learn.microsoft.com/azure/documentdb/how-to-build-java-console-app): a `MongoCredential.OidcCallback` whose `onRequest()` calls `DefaultAzureCredential.getTokenSync()` for scope `https://ossrdbms-aad.database.windows.net/.default` and returns `new OidcCallbackResult(token)`, passed as `MongoCredential.createOidcCredential(null).withMechanismProperty("OIDC_CALLBACK", oidcCallback)` (`mongodb-driver-sync` 5.4.0, `azure-identity` 1.15.4 on that page; the Entra ID page itself has only Python, TypeScript and C# tabs).

  Next to the existing Learn link, add the *Manage secondary Microsoft Entra ID identities* section of the same page. Remove the "or the current documented mechanism" and "verify current driver support" comments.
- **Fix the SCRAM least-privilege example.** `readWrite` on `orders` is rejected by the engine ("Roles specified are invalid ..."). Replace it with `readAnyDatabase` (read-only), with `readWriteAnyDatabase` + `clusterAdmin` granted together (read-write), or with a custom role created with `createRole` (custom roles and database- or collection-level privileges are in preview; `updateRole` is unsupported, use `grantPrivilegesToRole` / `revokePrivilegesFromRole`). Say that secondary users are created with `mongosh` as the admin, never by the app at startup.
- **Raise the rule priority to HIGH.** The model's default answer is wrong, so this rule corrects that answer rather than polishing an already-correct one.

### 5. New file `skills/security/security-redact-logs.md`

Covers secrets and connection details in logged errors; PHI/PII field redaction for AI apps is in section 6, and the two rules cross-link.

- **Incorrect:** `console.error(err)`, `logger.error(payload)`, or printing the connection error object at startup.
- **Correct:** a `logError(scope, err)` helper that logs only `name`, `code` and a redacted `message`, replacing `mongodb://` / `mongodb+srv://` URIs and `Bearer` tokens with placeholders. Add the Python equivalent with `logging`.
- On connect failure, log with the helper and exit. Return `{ error: "internal server error" }` to HTTP callers. Never log request bodies or documents.
- Add a "See also" line: "For PHI/PII fields in documents, prompts and agent memory, see [security-ai-sensitive-data](security-ai-sensitive-data.md)."

### 6. New file `skills/security/security-ai-sensitive-data.md`

````markdown
# security-ai-sensitive-data

**Category:** Security · **Priority:** HIGH

## Why it matters

In RAG and agent applications, DocumentDB documents flow into prompts, logs and agent-memory collections. Regulated fields (PHI, PII, account data) and connection secrets can leak through any of these paths even when the cluster itself is locked down.

## Incorrect

- Interpolating the connection string, or raw documents, into an LLM prompt or tool argument.
- `logger.info(doc)` on patient or customer records.
- Storing full chat transcripts that contain PII in an agent-memory collection.
- Querying by a client-supplied `patientId` or `tenantId` without checking that the caller is allowed to read it.

## Correct

- Read the connection URI from an environment variable or Azure Key Vault inside the tool, or use Microsoft Entra ID / managed identity (see [security-entra-rbac](security-entra-rbac.md)). The model calls typed tools such as `find_patient(patient_id)`, or the app uses the DocumentDB MCP server, which holds the connection server-side.
- Keep one field denylist, built from the patterns in `natural-language-querying` and extended with domain fields, and use it in both the prompt builder and a logging filter:

  ```python
  import logging

  SENSITIVE = {"patientId", "name", "dob", "ssn", "accountNumber", "clinicalNotes"}

  def redact(v):
      if isinstance(v, dict):
          return {k: ("[REDACTED]" if k in SENSITIVE else redact(x)) for k, x in v.items()}
      if isinstance(v, list):
          return [redact(x) for x in v]
      return v

  class RedactFilter(logging.Filter):
      def filter(self, record):
          if isinstance(record.args, dict):
              record.args = redact(record.args)
          return True
  ```

  Do not add vector fields (for example `embedding`) to the denylist; the vector must reach the `cosmosSearch` index.
- For connection URIs, tokens and error objects in logs, see [security-redact-logs](security-redact-logs.md).
- Call `authorize(user, patient_id)` before every query that takes a caller-supplied identifier.
- Store only identifiers (for example `conversationId`, `lastAppointmentId`) in agent-memory documents.
- Minimise or de-identify text before it reaches the model. For PHI, send it only to an endpoint covered by your organisation's agreements, for example an Azure OpenAI / Foundry deployment (see [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)).
- Check at startup that the LLM API key is set, and never log it.

## Encryption

Azure DocumentDB encrypts all data, backups and logs at rest with AES-256; use [security-cmk-encryption](security-cmk-encryption.md) when you must control the key, and [security-entra-rbac](security-entra-rbac.md) for identity.

Client-side field-level encryption (explicit CSFLE, where the application encrypts fields with the driver's `ClientEncryption` API before writing) is listed as supported for Azure DocumentDB ([Azure DocumentDB vs MongoDB Atlas](https://learn.microsoft.com/azure/documentdb/compare-mongodb-atlas), security table); there is no Learn how-to, so treat drivers and key providers as unvalidated. Automatic CSFLE (`autoEncryption` with a schema map) is not documented. Queryable Encryption is not supported: the engine rejects `encryptedFields` on `createCollection` ("encryptedFields not supported yet"). Encrypted fields cannot be filtered or indexed server-side; keep them out of query predicates and vector or search indexes.

## References

- [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security)
- [Data, privacy, and security for Foundry Models sold by Azure](https://learn.microsoft.com/azure/foundry/responsible-ai/openai/data-privacy)
````

The "For connection URIs, tokens and error objects in logs" bullet is the only addition to K35's original text; it cross-links the rule in section 5.

### 7. New file `skills/security/security-sample-readme-production-notes.md`

A copy-paste "Authentication, secrets and production notes" README block for generated samples:

- why the quickstart uses a SCRAM connection string, and that it is the admin credential and must not ship to production;
- use Entra ID in production (enable `MicrosoftEntraID`, register the managed identity, connect with `MONGODB-OIDC`);
- least privilege if a password is needed (a secondary user created with `mongosh` by the admin);
- secrets in Azure Key Vault, `.env` for local development only and gitignored;
- firewall restricted to known IPs, or a Private Endpoint with public access disabled;
- the app refuses URIs without `tls=true`;
- diagnostic settings and slow-query logs (`documentdb-monitoring`);
- the local gateway image on port 10260 with `--tlsAllowInvalidCertificates` is acceptable only locally.

### 8. `skills/security/security-tls-required.md`

Add a cross-link to `security-redact-logs.md`.

### 9. `skills/azure-deployment/SKILL.md` and `references/`

- **`SKILL.md`: replace the "Entra RBAC / CMK / diagnostic settings" bullet with:**

  > **Microsoft Entra ID auth** (recommended for production). New clusters allow native auth only. Run `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`, then register each identity as described in `documentdb-security` › security-entra-rbac. Azure role assignments never let a driver connect. Connection code: `documentdb-connection` › Authentication modes. CMK / diagnostics: `documentdb-security`, `documentdb-monitoring`.
- **`SKILL.md` Step 6b:** add `"authConfig": { "allowedModes": ["NativeAuth"] }` to the `az resource create --properties` JSON, with a comment explaining how to add `MicrosoftEntraID`.
- **`references/bicep-cluster-template.md`:** add `param authAllowedModes array = ['NativeAuth']` and `authConfig: { allowedModes: authAllowedModes }` under `properties`.
- **`references/terraform-cluster-template.md`:** add `authentication_methods = var.authentication_methods` on `azurerm_mongo_cluster` with `variable "authentication_methods" { default = ["NativeAuth"] }` (allowed values `NativeAuth`, `MicrosoftEntraID`; azurerm >= 4.55.0; `administrator_username` stays required while `NativeAuth` is present). Note that `azurerm_mongo_cluster_user` (same release) registers an Entra administrator (`identity_provider_type = "MicrosoftEntraID"`, `principal_type = "user" | "servicePrincipal"`, role `root`), so no `azapi` resource is needed for either step. Today the template never sets this, so Entra ID cannot be enabled from the kit's IaC path.

### 10. `skills/mcp-setup/SKILL.md`

- **Before the `CONNECTION_PROFILES` example, add:** "Use `authMode: "entra"` only if `az documentdb mongocluster show ... --query properties.authConfig.allowedModes` contains `MicrosoftEntraID` **and** the identity running the server is registered as a cluster user. Otherwise use `connectionString`. Always set `allowedHosts: ["*.mongocluster.cosmos.azure.com"]` on an `entra` profile: the server passes it through as the driver's `ALLOWED_HOSTS`, and without it the Node driver's default list (no Azure domain) rejects every Azure host. Either portal connection string (Self or Global read-write) may be used as `endpoint`; the wildcard matches both."
- **Extend "Auth errors":** "For Entra, confirm `MicrosoftEntraID` is in `allowedModes` and that the principal appears in `usersInfo` (or in the cluster's Entra admin list). `MongoInvalidArgumentError: Host ... is not valid for OIDC authentication with ALLOWED_HOSTS` means the profile has no `allowedHosts`."

### 11. `docs/SKILLS.md`

The skills table has one row per skill. Extend the `security/` row's topics (today "TLS, Private Endpoint, Microsoft Entra RBAC, CMK") to cover the three new rules: log redaction (`security-redact-logs`), sample README production notes (`security-sample-readme-production-notes`) and sensitive data in AI/LLM apps (`security-ai-sensitive-data`).

## Evidence

Run folders from the experiment (one run). For the auth runs see `02-readiness.json` → `confusions[Q06]` and `05-audit.json`.

- `runs/04-earnings-call-rag-assistant/20261124-190247/`: the cold answer said Entra ID is not supported on the wire endpoint, and the audit found no OIDC path in the app.
- `runs/19-proactive-outreach-orchestration/20261124-205844/`: the cold answer invented `MONGODB-AZUREAD` and passed the token as a password.
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/`: the cold answer described account primary/secondary keys.
- `runs/14-customer-complaint-classifier/20261124-201931/`: decisions D005/D011 skipped Entra as "complex OIDC setup".
- `runs/16-loyalty-points-ledger/20261124-184937/`: `doc-gaps.md` logged a high-severity gap for a missing Node + Entra example, and the build shipped SCRAM.
- `runs/09-clinical-notes-de-identification/20261124-194349/`: `doc-gaps.md` "PHI and external LLMs" (high).
- `runs/19-care-coordination-multi-agent/20261124-195730/`: `05-audit.json` P31, PHI and logging; CSFLE suggested, not assessable.
- `runs/14-dynamic-pricing-engine/20261124-184622/`: `doc-gaps.md` "Not sending secrets to LLMs" (high).
- `runs/01-patient-record-summarizer-rag/20261124-192917/`: PHI logging and app-layer authorization.
- `runs/02-transaction-categorization-agent/20261124-190028/`: PII sent to the LLM without redaction guidance.

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- **Driver floors for MONGODB-OIDC** (facts; whether the skill states them is a maintainer decision, see Open question 1): PyMongo 4.7 (changelog 4.7.0, 2024-04-24), Node `mongodb` 6.7.0 (release notes v6.7, 2024-05-29), Java driver 5.1 (`createOidcCredential` Javadoc `@since 5.1`; r5.0.0 has no OIDC), .NET `MongoDB.Driver` 2.25.0 (release 2024-04-12, CSHARP-4448); `AsyncMongoClient` exists from PyMongo 4.9 (beta) and is GA from 4.13. Sources: DECISIONS.md topic 4 items 4.1-4.5 (mongo-python-driver changelog and PyPI; node-mongodb-native release v6.7.0 and npm registry; mongo-java-driver MongoCredential.java at master and r5.0.0; mongo-csharp-driver release v2.25.0; PyMongo release notes 4.9 and 4.13).
- **Java callback**: Learn publishes one, so the filing adds it (section 4). `how-to-build-java-console-app` (updated 2026-11-23) implements `MongoCredential.OidcCallback` calling `DefaultAzureCredential.getTokenSync()` for the `ossrdbms-aad` scope and uses `createOidcCredential(null).withMechanismProperty("OIDC_CALLBACK", ...)` with `mongodb-driver-sync` 5.4.0 and `azure-identity` 1.15.4; not exercised by this experiment. Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-build-java-console-app; https://github.com/Azure-Samples/documentdb-samples/tree/main/ai/vector-search-java (also connects with MONGODB-OIDC).
- **Roles for nonadministrative Entra identities**: grant `readWriteAnyDatabase` and `clusterAdmin` together; `readAnyDatabase` is the only standalone built-in. The RBAC page (updated 2026-11-23) says the two "must be granted together", and the engine's `ValidateAndObtainUserRole()` accepts exactly {clusterAdmin, readWriteAnyDatabase}, {readAnyDatabase}, or readWriteAnyDatabase alone only behind a flag whose compiled default is off. Whether Azure runs that flag on (which would make the secondary-users page's standalone table right) stays an engineering question in DECISIONS.md, but granting both is accepted in either state, so the filing follows the RBAC page. Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control; https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/users.c; https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/configs/feature_flag_configs.c; https://learn.microsoft.com/en-us/azure/documentdb/secondary-users.
- **`--type` for `microsoft-entra-user assign`**: exactly `User` and `ServicePrincipal`; a service principal or managed identity is registered with `--type ServicePrincipal` and its object ID (`principalId`), not the client ID; the CLI maps the flag onto the ARM users resource's `principalType` and sends `--object-id` as the `users/{principalId}` path segment. Sources: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster/microsoft-entra-user#az-documentdb-mongocluster-microsoft-entra-user-assign; https://github.com/Azure/azure-cli-extensions/blob/main/src/documentdb/azext_documentdb/custom.py; https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (object-ID paragraph and REST/Bicep/Terraform principal-type rule).
- **`ALLOWED_HOSTS` value**: both `*.azure.com` (Learn) and `*.mongocluster.cosmos.azure.com` (MCP README, kit README, Mongoose tutorial) match both host forms; the kit recommends the narrower `*.mongocluster.cosmos.azure.com`. The Node driver checks `ALLOWED_HOSTS` after SRV resolution for every custom OIDC callback and its default list has no Azure domain, so the property is required in Node; PyMongo checks it only for human callbacks. Sources: https://github.com/mongodb/node-mongodb-native/blob/main/src/mongo_client.ts and src/cmap/auth/mongo_credentials.ts (DEFAULT_ALLOWED_HOSTS); https://github.com/mongodb/specifications/blob/master/source/auth/auth.md; https://github.com/mongodb/mongo-python-driver/blob/master/pymongo/auth_oidc_shared.py; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose; microsoft/documentdb-mcp src/context/documentdb.ts:37.
- **Terraform `authConfig`**: `azurerm_mongo_cluster` exposes `authentication_methods` (`NativeAuth`, `MicrosoftEntraID`) since azurerm 4.55.0 (2025-12-04, #31100, renamed from `auth_config_allowed_modes` in #31209), and `azurerm_mongo_cluster_user` (same release, #31205) registers an Entra administrator; `azapi` is optional. Sources: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/mongo_cluster; https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/mongo_cluster_user; https://github.com/hashicorp/terraform-provider-azurerm/blob/main/CHANGELOG-v4.md (4.55.0).
- **Learn TypeScript sample units**: the Learn sample is wrong. `expiresOnTimestamp` is epoch milliseconds (`@azure/core-auth`) and `expiresInSeconds` is seconds (Node driver), so `expiresOnTimestamp - Math.floor(Date.now()/1000)` is off by a factor of about 1,000; the correct form is the JavaScript pivot's `Math.floor((expiresOnTimestamp - Date.now()) / 1000)`, which this filing's snippet uses. Runtime impact is nil today because the Node driver's TokenCache never reads the value. The doc fix is recorded in DECISIONS.md (topic 5 Learn fixes) for the Learn filings, not this kit PR. Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (TypeScript tab); https://learn.microsoft.com/en-us/azure/documentdb/how-to-build-nodejs-console-app (TS vs JS pivot); https://learn.microsoft.com/en-us/javascript/api/@azure/core-auth/accesstoken; https://www.mongodb.com/docs/drivers/node/current/security/authentication/oidc/; https://github.com/mongodb/node-mongodb-native/blob/main/src/cmap/auth/mongodb_oidc/token_cache.ts.
- **When the `.global.` host is required**: never. On a single cluster the Self (`<cluster>.mongocluster.cosmos.azure.com`) and Global read-write (`<cluster>.global.mongocluster.cosmos.azure.com`) strings are interchangeable ("you can use either connection string indiscriminately"); the Global string exists only on the primary and keeps writes working across a replica promotion, while the old primary's Self string becomes read-only and replica clusters expose only Self strings. Kit default snippets show the plain host with that note and tell agents to take the host from the returned connection string, never to construct it from the cluster name (section 1a updated). Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ('Get cluster credentials'); https://learn.microsoft.com/en-us/azure/documentdb/how-to-cluster-replica#use-connection-strings; https://learn.microsoft.com/en-us/azure/documentdb/cross-region-replication; https://learn.microsoft.com/en-us/azure/documentdb/how-to-private-link; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose; https://learn.microsoft.com/en-us/training/modules/create-configure-azure-documentdb-cluster/3-connect-to-cluster.
- **Explicit CSFLE and Queryable Encryption**: explicit client-side field-level encryption is listed as supported (compare-mongodb-atlas security table "✅ Yes"; release notes 2025-10-10 "[Preview] schema enforcement with CSFLE integration"), with no Learn how-to; Queryable Encryption is not supported, the engine rejects `encryptedFields` ("encryptedFields not supported yet", create_collection_view.c:526-529). `security-ai-sensitive-data.md` now states this (section 6). Automatic CSFLE stays open (Open question 2). Sources: https://learn.microsoft.com/en-us/azure/documentdb/compare-mongodb-atlas; https://learn.microsoft.com/en-us/azure/documentdb/release-notes; https://github.com/documentdb/documentdb (CHANGELOG.md v0.107-0; pg_documentdb/src/configs/feature_flag_configs.c:600-601; pg_documentdb/src/commands/create_collection_view.c:526-529); https://www.mongodb.com/docs/manual/core/csfle/reference/compatibility.md; https://www.mongodb.com/docs/manual/core/queryable-encryption/fundamentals/encrypt-and-query.md.
- **Learn follow-up for CSFLE**: yes; DECISIONS.md records it as a Learn fix for the Learn filings (add a CSFLE/QE sentence to [Secure your cluster](https://learn.microsoft.com/azure/documentdb/security), qualify the bare checkmark on compare-mongodb-atlas, and change the `compactStructuredEncryptionData | N/A` row on compatibility-query-language to "No"). No SME needed; not part of this kit PR. Sources: DECISIONS.md topic 13 'Learn and reference fixes'.

## Open questions

1. **Should the kit state driver version minimums at all?** Maintainer decision (DECISIONS.md topic 4, 4.11-open). The floors themselves are settled (see Resolved). DECISIONS.md's best guess, which this filing follows: state floors only where a feature is gated (MONGODB-OIDC: PyMongo 4.7, Node 6.7.0, Java 5.1, .NET 2.25; `AsyncMongoClient` GA: PyMongo 4.13) and otherwise say "resolve the current stable release and pin exactly". The observed cost of saying nothing was 13 runs failing on nonexistent npm versions and 5 on Motor/Beanie 1 stacks.
2. [needs SME confirmation] **Automatic CSFLE.** Is automatic client-side field-level encryption (driver `autoEncryption` with a schema map or server-side `$jsonSchema` `encrypt`, via mongocryptd or crypt_shared) supported and validated on Azure DocumentDB? Learn has only a bare checkmark and a [Preview] release note about "schema enforcement with CSFLE integration"; nothing says which drivers or libmongocrypt versions were tested, whether `listCollections` returns the `encrypt` validator, or how the preview is enabled (the engine flag defaults to true, but the release-notes banner says [Preview] items need a support request). Until answered, section 6 says only that automatic CSFLE is not documented.
3. [needs SME confirmation] **PHI endpoint wording.** Is "for PHI, use an endpoint covered by your organisation's agreements, for example an Azure OpenAI / Foundry deployment" (linking the Foundry data-privacy page) acceptable wording with no compliance claim? This is a legal/comms judgement for the DocumentDB and Foundry teams, not a fact a source settles; Microsoft's HIPAA page stresses that BAA coverage comes through the Product Terms for in-scope services and does not by itself make a customer compliant. DECISIONS.md's best guess: acceptable as drafted; if reviewers want a compliance pointer, link the [HIPAA offering page](https://learn.microsoft.com/azure/compliance/offerings/offering-hipaa-us) and "Cloud services in audit scope" rather than asserting coverage for DocumentDB or Azure OpenAI.

## Source drafts

- 016-believes-entra-id-is-not-supported-for-data-plane-auth-only-.md (base)
- 014-believes-authentication-is-account-key-username-password-scr.md
- 017-believes-an-entra-access-token-is-passed-via-the-wrong-mecha.md
- 018-unaware-that-entra-id-is-an-opt-in-cluster-setting-authconfi.md
- 041-believes-vcore-lacks-or-restricts-platform-features-it-suppo.md (auth part only; change-stream and transaction notes go to K04/K15)
- 101-security-and-production-hardening-guidance-absent-single-adm.md (Entra, least-privilege, TLS-guard, log-redaction and README-block parts; its host-suffix fix goes to K01)
- 122-security-and-compliance-practices-for-ai-applications-on-azu.md

## Merged from

- K03: connection and security skills: Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode, with the enable/registration step and runnable per-driver examples
- K35: security skill: add a rule for sensitive data in AI/LLM applications (PHI/PII redaction, no secrets in prompts, app-layer authorization)
