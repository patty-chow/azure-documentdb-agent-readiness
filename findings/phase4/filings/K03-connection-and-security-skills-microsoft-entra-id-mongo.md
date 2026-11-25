---
id: K03
title: "connection and security skills: Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode, with the enable/registration step and runnable per-driver examples"
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
open_questions: 9
---

# connection and security skills: Microsoft Entra ID (MONGODB-OIDC) as a supported data-plane auth mode, with the enable/registration step and runnable per-driver examples

## What happens today

An agent that writes connection code for Azure DocumentDB loads `skills/connection/SKILL.md`. Its whole "Authentication" section is two bullets: "Default mechanism: `SCRAM-SHA-256`" and "Credentials are managed through the Azure portal". It does not mention Microsoft Entra ID, and `skills/driver/SKILL.md` does not mention auth at all.

The only application-side Entra guidance is `skills/security/security-entra-rbac.md` (priority MEDIUM). An agent reaches it only if it opens the security skill and then follows the sub-link. Its "Correct" block cannot authenticate as written:

- It has `authMechanism: "MONGODB-OIDC", // or the current documented mechanism`, with `// credentialProvider: Azure Managed Identity` left as a comment, and it tells the reader to "verify current driver support/spec in the official docs".
- It sets no `authMechanismProperties`, so there is no `OIDC_CALLBACK` and no `TOKEN_RESOURCE`.
- It never says that Entra has to be enabled on the cluster (`authConfig.allowedModes`) or that each identity has to be registered as a cluster user.
- Its least-privilege SCRAM example grants `{ role: "readWrite", db: "orders" }`, which is not one of the roles Learn lists for secondary users.

`skills/azure-deployment/SKILL.md` (near line 311) has only "Entra RBAC / CMK / diagnostic settings. See `documentdb-security`". The Bicep and Terraform references never set `authConfig`. `skills/mcp-setup/SKILL.md` uses `authMode: "entra"` but never says how to tell whether the cluster allows it. The kit README calls Entra/OIDC the *recommended* mode for the MCP server, yet the skills never tell application code the same thing.

The Learn page [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control) already documents all of this: the enable command, admin and non-admin registration, the token scope, and Python, TypeScript and C# callbacks. The gap is in the kit.

## Why it matters

We ran one agent-readiness experiment: 100 Azure DocumentDB sample prompts, each built by gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers. All counts below come from that single run and will move on a re-run.

- **98 of 100 samples** answered the cold-quiz question "Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID?" wrong or partly wrong. This was recounted from each run's `02-readiness.json`.
- The wrong answers fell into three groups, one per member draft:
  - **"Control-plane only" (67 samples, draft 016).** The model said Entra is control-plane only and that the MongoDB wire endpoint takes SCRAM only. This is the Azure Cosmos DB for MongoDB (RU) prior.
  - **Invented mechanisms (15 samples, draft 017).** Examples: passing the token as a SCRAM password, `MONGODB-AZUREAD`, `PLAIN` with `$external`, `OAUTHBEARER`/`GSSAPI`, and X.509.
  - **Opt-in step missing (17 samples, draft 018).** 15 said Entra is unavailable on the wire protocol or assumed it works without enabling anything on the cluster; 2 described the Cosmos DB for NoSQL model (account keys, or Azure RBAC role assignments on the account).
  - The three groups sum to 99 because one sample falls in two of them; they cover 98 distinct samples.
- A related cold question about the connection-string format got the auth part wrong in 35 samples (36 findings, draft 014). Those answers used the `:10255` "the password is the account key" form.

**Effect on the builds:** most builds shipped a single admin SCRAM `DOCUMENTDB_URI`. A recount of app source files finds `MONGODB-OIDC` in only 23 of the 100 builds. The audit stage repeatedly flagged that Entra was not shown or not explained.

In one run (`14-customer-complaint-classifier`), the builder explicitly skipped OIDC to "avoid complex OIDC setup". The harness-supplied URI was the main reason there, but the kit gave it no cheap working alternative.

Across all six member drafts the theme touches **99 distinct samples**: the 98 above plus one build (`03-medication-interaction-checker`) whose practice audit flagged a SCRAM-only app with no Entra path (draft 101).

## Proposed change

All of this PR's edits to a given file are listed together per section (sections 1 and 6 both touch `skills/connection/SKILL.md`, in different subsections). This PR does **not** cover the following:

- Host-suffix fixes (`.mongocluster.documentdb.azure.com` → `.mongocluster.cosmos.azure.com`) and the connection-string `retryWrites` line: these are in K01.
- Change-stream and transaction rules: these are in K04 and K15.
- PHI/PII redaction in prompts and app-layer authorization for AI apps: K35. Section 6 below keeps draft 101's connection-error redaction helper, which K35 does not include.

### 1. `skills/connection/SKILL.md`: replace "### Authentication"

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

client = MongoClient(
    f"mongodb+srv://{CLUSTER}.global.mongocluster.cosmos.azure.com/",
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
const client = new MongoClient(`mongodb+srv://${CLUSTER}.global.mongocluster.cosmos.azure.com/`, {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const t = await credential.getToken(SCOPE);
      // expiresOnTimestamp is in milliseconds
      return { accessToken: t.token, expiresInSeconds: Math.max(0, Math.floor((t.expiresOnTimestamp - Date.now()) / 1000)) };
    },
    ALLOWED_HOSTS: ["*.azure.com"],
  },
});
```

Mongoose: pass the same options to `mongoose.connect(uri, options)`; they go through to the driver.

**Fall back to SCRAM-SHA-256 only when** the cluster does not have Entra enabled, the runtime has no Azure identity (for example a CI machine outside Azure without `az login`), or the client is a third-party tool that cannot run an OIDC callback. Then use a least-privilege secondary user created by an admin, never the built-in admin. `DefaultAzureCredential` covers `az login` locally and managed identity in Azure, so the same Entra code runs in both places.

Learn lists both host forms: `<cluster>.global.mongocluster.cosmos.azure.com` or `<cluster>.mongocluster.cosmos.azure.com` (see Open question 9 on when `.global.` is required). mongosh/Compass on an Azure host with a managed identity:
`mongodb+srv://<client-id>@<cluster>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000&authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:https://ossrdbms-aad.database.windows.net`

Do not tell users Entra ID is "control-plane only" or unsupported on the MongoDB wire protocol; that was Azure Cosmos DB for MongoDB (RU), not Azure DocumentDB. Cluster setup, user registration, other drivers: `documentdb-security` › security-entra-rbac. Full walkthrough: https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control
````

Also add a "Related skills" line to `skills/connection/SKILL.md` (it has none today) that names `documentdb-security` › security-entra-rbac.

### 2. `skills/security/security-entra-rbac.md`

- **Add before "Incorrect": "How authorization works on Azure DocumentDB".**
  - **There are no account keys.** Native auth is a SCRAM user + password. Cosmos DB "primary key" and "resource token" auth do not exist here.
  - **Entra is opt-in per cluster.** Enable it with `az documentdb mongocluster update --name <cluster> --resource-group <rg> --auth-allowed-modes NativeAuth MicrosoftEntraID`. Keep `NativeAuth` until an Entra principal has connected. Check the result with `az documentdb mongocluster show ... --query properties.authConfig`.
  - **Enabling the mode grants nobody access.** Azure role assignments on the `mongoClusters` resource control management only. Data access comes from MongoDB roles on a principal registered inside the cluster.
  - **Administrator (`root` on `admin`).** Register with `az documentdb mongocluster microsoft-entra-user assign --cluster-name <cluster> --resource-group <rg> --object-id <object-id> --type <principal-type> --role db=admin role=root`, or with the ARM/Bicep `Microsoft.DocumentDB/mongoClusters/users` resource (`identityProvider.type: MicrosoftEntraID`, `principalType: user | servicePrincipal`; the resource name is the principal's object ID). The ARM endpoint supports administrative registration only.
  - **Nonadministrative (least privilege).** An Entra admin runs `createUser` with the principal's **object ID**, not its client ID:
    - roles `clusterAdmin` + `readWriteAnyDatabase`, or `readAnyDatabase` for read-only;
    - `customData: { IdentityProvider: { type: "MicrosoftEntraID", properties: { principalType: "servicePrincipal" } } }`.

    Verify with `db.getSiblingDB("admin").runCommand({ usersInfo: 1 })`. ARM user listings do not show these database-only users.
- **Add a second "Incorrect" block.** List the mechanisms that fail:
  - an Entra token passed as a SCRAM password;
  - `MONGODB-AZUREAD`;
  - `PLAIN`, `GSSAPI` or `MONGODB-X509` with `authSource=$external`;
  - raw `OAUTHBEARER`;
  - an Atlas human-flow OIDC configuration copied unchanged (no callback and no `TOKEN_RESOURCE` for the `ossrdbms-aad` resource).

  Note that `$external` itself is correct for MONGODB-OIDC. Drivers set it by default.
- **Replace the "Correct" block.** It gets three things:
  - the prerequisites above;
  - "Python and Node: see `documentdb-connection` › Authentication modes";
  - the .NET form from Learn: `MongoCredential.CreateOidcCredential(new AzureIdentityTokenHandler(new DefaultAzureCredential(), tenantId))`, where the handler implements `IOidcCallback` for the same scope.

  Add a Java `OIDC_CALLBACK_KEY` example only after verification (see Open questions). Next to the existing Learn link, add the *Manage secondary Microsoft Entra ID identities* section of the same page. Remove the "or the current documented mechanism" and "verify current driver support" comments.
- **Fix the SCRAM least-privilege example.**
  - Replace `readWrite` on `orders` with a listed role (`readAnyDatabase` / `readWriteAnyDatabase`) or a database-scoped custom role (preview).
  - Say that secondary users are created with `mongosh` as the admin, never by the app at startup.
- **Raise the rule priority to HIGH.** The model's default answer is wrong, so this rule corrects that answer rather than polishing an already-correct one.

### 3. `skills/azure-deployment/SKILL.md` and `references/`

- **Replace the "Entra RBAC / CMK / diagnostic settings" bullet with:**

  > **Microsoft Entra ID auth** (recommended for production). New clusters allow native auth only. Run `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`, then register each identity as described in `documentdb-security` › security-entra-rbac. Azure role assignments never let a driver connect. Connection code: `documentdb-connection` › Authentication modes. CMK / diagnostics: `documentdb-security`, `documentdb-monitoring`.
- **Step 6b:** add `"authConfig": { "allowedModes": ["NativeAuth"] }` to the `az resource create --properties` JSON, with a comment explaining how to add `MicrosoftEntraID`.
- **`references/bicep-cluster-template.md`:** add `param authAllowedModes array = ['NativeAuth']` and `authConfig: { allowedModes: authAllowedModes }` under `properties`.
- **`references/terraform-cluster-template.md`:** add the equivalent setting (see Open questions).

### 4. `skills/mcp-setup/SKILL.md`

- **Before the `CONNECTION_PROFILES` example, add:** "Use `authMode: "entra"` only if `az documentdb mongocluster show ... --query properties.authConfig.allowedModes` contains `MicrosoftEntraID` **and** the identity running the server is registered as a cluster user. Otherwise use `connectionString`."
- **Extend "Auth errors":** "For Entra, confirm `MicrosoftEntraID` is in `allowedModes` and that the principal appears in `usersInfo` (or in the cluster's Entra admin list)."

### 5. `skills/driver/SKILL.md` and `skills/security/SKILL.md`

- **Driver skill:** after the singleton rule, add "Authentication: SCRAM-SHA-256 or Microsoft Entra ID (`MONGODB-OIDC`). See `documentdb-connection` › Authentication modes."
- **Security skill:** update the security-entra-rbac index line to "Enable Entra on the cluster, register principals, connect with MONGODB-OIDC; least-privilege secondary users".

### 6. Draft 101's hardening helpers: `skills/connection/SKILL.md` and two new security rules

- **TLS guard in `skills/connection/SKILL.md`.** Add a small `require_secure_uri(uri)` helper (Python, with a Node equivalent). It raises unless the URI has `tls=true` (or `ssl=true`), and it refuses `tlsAllowInvalidCertificates=true` or `tlsInsecure=true` outside local development.
- **New rule `skills/security/security-redact-logs.md`.**
  - Incorrect: `console.error(err)`, `logger.error(payload)`, or printing the connection error object at startup.
  - Correct: a `logError(scope, err)` helper that logs only `name`, `code` and a redacted `message`, replacing `mongodb://` / `mongodb+srv://` URIs and `Bearer` tokens with placeholders. Add the Python equivalent with `logging`.
  - On connect failure, log with the helper and exit. Return `{ error: "internal server error" }` to HTTP callers. Never log request bodies or documents.
  - Cross-link it from `security-tls-required.md`.
- **New rule `skills/security/security-sample-readme-production-notes.md`.** A copy-paste "Authentication, secrets and production notes" README block for generated samples:
  - why the quickstart uses a SCRAM connection string, and that it is the admin credential and must not ship to production;
  - use Entra ID in production (enable `MicrosoftEntraID`, register the managed identity, connect with `MONGODB-OIDC`);
  - least privilege if a password is needed (a secondary user created with `mongosh` by the admin);
  - secrets in Azure Key Vault, `.env` for local development only and gitignored;
  - firewall restricted to known IPs, or a Private Endpoint with public access disabled;
  - the app refuses URIs without `tls=true`;
  - diagnostic settings and slow-query logs (`documentdb-monitoring`);
  - the local gateway image on port 10260 with `--tlsAllowInvalidCertificates` is acceptable only locally.
- **Wire-up.** List both rules in `skills/security/SKILL.md` and `docs/SKILLS.md`. Add one line to "When Creating Code" in `skills/connection/SKILL.md`: every generated app that reads `DOCUMENTDB_URI` calls the TLS guard, uses the redacting logger and includes the README block.

## Evidence

Run folders from the experiment. See `02-readiness.json` → `confusions[Q06]` and `05-audit.json` in each.

- `runs/04-earnings-call-rag-assistant/20261124-190247/`: the cold answer said Entra ID is not supported on the wire endpoint, and the audit found no OIDC path in the app.
- `runs/19-proactive-outreach-orchestration/20261124-205844/`: the cold answer invented `MONGODB-AZUREAD` and passed the token as a password.
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/`: the cold answer described account primary/secondary keys.
- `runs/14-customer-complaint-classifier/20261124-201931/`: decisions D005/D011 skipped Entra as "complex OIDC setup".
- `runs/16-loyalty-points-ledger/20261124-184937/`: `doc-gaps.md` logged a high-severity gap for a missing Node + Entra example, and the build shipped SCRAM.

## Open questions

1. [needs SME confirmation] **Minimum driver versions for MONGODB-OIDC.**
   - Drafts cite Node `mongodb` 6.7.0 and PyMongo 4.7.0, from the driver release notes.
   - PyMongo 4.9+ is needed for `AsyncMongoClient`.
   - .NET and Java minimums are unverified.

   Should the skill state minimums at all?
2. [needs SME confirmation] **Java callback.** The Java `OIDC_CALLBACK_KEY` callback is not on Learn. Should we add a verified Java example or leave Java out?
3. [needs SME confirmation] **Drafts disagree on retryable writes.** Learn's connection string and every snippet here use `retrywrites=false`. Some drafts in this experiment say retryable writes are unsupported and cause write errors. Others say Learn makes no such claim and the setting is only a recommendation. What is the engineering position? This PR adds no rationale either way.
4. [needs SME confirmation] **Roles for nonadministrative Entra identities.** The Entra page says `readWriteAnyDatabase` and `clusterAdmin` must be granted together. The secondary-users page lists them as separate roles, with a `validate ... repair` caveat for `readWriteAnyDatabase`. Which is current?
5. [needs SME confirmation] **`--type` value for `microsoft-entra-user assign`.** Learn's example shows `User`. The drafts disagree on whether a managed identity or service principal takes `ServicePrincipal`. What are the accepted values?
6. [needs SME confirmation] **`ALLOWED_HOSTS` value.** Learn uses `*.azure.com`, while microsoft/documentdb-mcp uses `*.mongocluster.cosmos.azure.com`. Which should the kit recommend?
7. [needs SME confirmation] **Terraform `authConfig`.** What is the `azurerm_mongo_cluster` attribute for `authConfig.allowedModes`, and is it exposed in provider 4.x? If it is not, is `azapi_update_resource` the recommended route?
8. [needs SME confirmation] **Learn TypeScript sample units.** Learn's sample computes `expiresInSeconds` as `expiresOnTimestamp - Date.now()/1000`, which subtracts seconds from milliseconds. The snippet here converts to seconds first. Is the Learn sample wrong? If so, it should get separate doc feedback.
9. [needs SME confirmation] **When the `.global.` host is required.** Learn lists both host forms. Draft 041 says to use `<cluster>.global.mongocluster.cosmos.azure.com` when the cluster has a cross-region replica and that either works otherwise; draft 017 says the non-global host works for a single cluster. Is that the rule, and should the kit's default snippets use the non-global host to match the canonical connection string?

## Source drafts

- 016-believes-entra-id-is-not-supported-for-data-plane-auth-only-.md (base)
- 014-believes-authentication-is-account-key-username-password-scr.md
- 017-believes-an-entra-access-token-is-passed-via-the-wrong-mecha.md
- 018-unaware-that-entra-id-is-an-opt-in-cluster-setting-authconfi.md
- 041-believes-vcore-lacks-or-restricts-platform-features-it-suppo.md (auth part only; change-stream and transaction notes go to K04/K15)
- 101-security-and-production-hardening-guidance-absent-single-adm.md (Entra, least-privilege, TLS-guard, log-redaction and README-block parts; its host-suffix fix goes to K01)
