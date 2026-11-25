---
title: "documentdb-security: replace placeholder Entra snippet with working MONGODB-OIDC code per driver, add tls=true URI guard, redacting logger, and a drop-in "Authentication, secrets and production notes" README block"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 23
findings: 35
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# documentdb-security: ship working Entra ID (MONGODB-OIDC) code, a `tls=true` URI guard, a redacting logger, and a drop-in README "Authentication, secrets and production notes" block

## What happens today

`skills/security/security-entra-rbac.md` tells the agent to prefer Microsoft Entra ID, but its "Correct" example is not runnable:

```javascript
const client = new MongoClient(uri, {
  authMechanism: "MONGODB-OIDC", // or the current documented mechanism
  // credentialProvider: Azure Managed Identity
  tls: true
});
```

It also uses a host suffix that does not exist (`prod-ddb.mongocluster.documentdb.azure.com`; the service suffix is `.mongocluster.cosmos.azure.com`) and shows `createUser` with `{ role: "readWrite", db: "orders" }`, which is not one of the native roles Learn lists for secondary users (`readAnyDatabase`, `readWriteAnyDatabase`, `clusterAdmin`, or a database/collection-scoped custom role). `skills/connection/SKILL.md` has an "Authentication" section that names only `SCRAM-SHA-256`. The kit already has `security-tls-required.md` (do not set `tlsAllowInvalidCertificates` / `tlsAllowInvalidHostnames`), `security-private-endpoint.md` (Private Endpoint / firewall) and `local-deployment/local-env-driven-config.md` (gate TLS relaxation on an env flag), but these are prose rules: nothing gives the agent a URI validator it can call, a safe logger, or README text for production hardening, and none of them is referenced from `connection/SKILL.md` "When Creating Code".

## Why it matters

In a 100-sample run with gpt-5-mini (kit skills + DocumentDB/Azure/Learn MCP), **23 samples (35 audit findings)** were flagged for the same cluster of violations: single admin `DOCUMENTDB_URI` with no Entra ID or least-privilege user, no Key Vault guidance, no `tls=true` check or rejection of `tlsAllowInvalidCertificates`, no firewall/Private Link note, `console.error(err)` / full-payload logging, full error printed on connect failure, and READMEs that say only "set DOCUMENTDB_URI". Counting all buckets, 28 of 100 samples hit at least one of these.

The model prior is actively wrong here: the cold-quiz question "Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID?" was a confusion in essentially every run, and in 21 runs the cold answer said Entra ID is *not* a data-plane auth path for this service. The kit corrects the belief but not the behavior: in `14-customer-complaint-classifier` the builder logged D005 and D011, choosing SCRAM because the run environment already supplied `DOCUMENTDB_URI` and Entra/OIDC would "add complexity and extra secrets management" (D005: "avoids complex OIDC setup"). The harness-provided URI was the main driver; the kit's placeholder snippet gave it no cheap alternative to reach for. The auditor then cited the kit's own `security/SKILL.md` and `connection/SKILL.md` as the violated practice (e.g. 17-seasonal-trend-spotter P02/P16), so the rule exists but is not actionable.

## Proposed change

### 1. `skills/security/security-entra-rbac.md` — make the example real

Replace the placeholder "Correct" block with the Learn-verified code (from https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control#connect-using-microsoft-entra-id-in-code), fix the host suffix in the "Incorrect" block, and add the enable/register CLI:

```bash
# Enable Entra auth (keep NativeAuth until Entra principals are verified)
az documentdb mongocluster update -n <cluster> -g <rg> --auth-allowed-modes NativeAuth MicrosoftEntraID
# Register the app's managed identity / SP (object ID, not client ID) as an admin principal
az documentdb mongocluster microsoft-entra-user assign --object-id <object-id> --cluster-name <cluster> -g <rg> --type ServicePrincipal --role db=admin role=root   # Learn's example uses --type User for a human principal
```

```python
# pymongo >= 4.7, azure-identity
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential): self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        token = self.credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        return OIDCCallbackResult(access_token=token)

client = MongoClient(
    f"mongodb+srv://{CLUSTER}.mongocluster.cosmos.azure.com/",
    tls=True, retryWrites=False, maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
)
# Same kwargs work for pymongo.AsyncMongoClient (preferred over Motor).
```

```javascript
// mongodb >= 6.x, @azure/identity
const { MongoClient } = require("mongodb");
const { DefaultAzureCredential } = require("@azure/identity");
const credential = new DefaultAzureCredential();
const client = new MongoClient(`mongodb+srv://${CLUSTER}.mongocluster.cosmos.azure.com/`, {
  tls: true, retryWrites: false, maxIdleTimeMS: 120000,
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const t = await credential.getToken("https://ossrdbms-aad.database.windows.net/.default");
      return { accessToken: t.token, expiresInSeconds: Math.floor(t.expiresOnTimestamp / 1000) - Math.floor(Date.now() / 1000) };
    },
    ALLOWED_HOSTS: ["*.mongocluster.cosmos.azure.com"],
  },
});
// Mongoose: mongoose.connect(uri, sameOptions) — options pass through to the driver.
// Note: expiresOnTimestamp is in milliseconds. Learn's TypeScript sample subtracts seconds from it directly;
// divide by 1000 as above. Learn uses ALLOWED_HOSTS ['*.azure.com']; the narrower pattern here also matches *.global.mongocluster.cosmos.azure.com.
```

Replace the SCRAM least-privilege example with what Learn actually supports (https://learn.microsoft.com/azure/documentdb/secondary-users): secondary users are created with `mongosh` as the built-in admin (ARM/CLI/Bicep do not create them); built-in roles are cluster-wide (`readAnyDatabase` for read-only, `readWriteAnyDatabase` for read-write across databases, `clusterAdmin` for supported cluster administration; for `readWriteAnyDatabase` Learn currently requires a one-time `validate ... repair: true` pass per existing collection); for a single-database or single-collection app create a database-scoped custom role (`createRole` with `resource: { db: "<appdb>", collection: "" }` and `actions: ["find","insert","update","delete"]`; custom roles are preview and cover data actions only, not index or collection lifecycle) and assign it. Note that the Entra page (how-to-connect-role-based-access-control) still states that for nonadministrative Entra identities `readWriteAnyDatabase` and `clusterAdmin` must be assigned together; the rule should say so for the Entra path. Note the Entra equivalent (`createUser` with the principal **object ID**, not the client ID, and `customData: { IdentityProvider: { type: "MicrosoftEntraID", properties: { principalType: "user" | "servicePrincipal" } } }`). Keep the "rotate; prefer Entra" line.

### 2. `skills/connection/SKILL.md` — Authentication section + two helpers

Change "Default mechanism: SCRAM-SHA-256" to list both mechanisms with a one-line pointer to the rule above, and add:

```python
from urllib.parse import urlsplit, parse_qs
def require_secure_uri(uri: str) -> str:
    q = {k.lower(): v[-1].lower() for k, v in parse_qs(urlsplit(uri).query).items()}
    if q.get("tls", q.get("ssl")) != "true":
        raise ValueError("DOCUMENTDB_URI must include tls=true")
    if q.get("tlsallowinvalidcertificates") == "true" or q.get("tlsinsecure") == "true":
        raise ValueError("refusing tlsAllowInvalidCertificates/tlsInsecure outside local dev")
    return uri
```

```javascript
// Log the shape of an error, never the object: err objects and payloads can carry URIs, tokens, prompts or PHI.
const redact = (s) => String(s ?? "").replace(/mongodb(\+srv)?:\/\/[^\s"']+/gi, "mongodb://<redacted>").replace(/Bearer [A-Za-z0-9._-]+/g, "Bearer <redacted>");
function logError(scope, err) { console.error(JSON.stringify({ scope, name: err?.name, code: err?.code, message: redact(err?.message) })); }
```

Rule text: on connect failure log `logError("db.connect", err)` and exit; return `{ error: "internal server error" }` to HTTP callers; never log request bodies or documents.

### 3. New rule `skills/security/security-sample-readme-production-notes.md`

A copy-paste README block the builder drops into every generated sample:

```markdown
## Authentication, secrets and production notes
- **Why this quickstart uses a connection string.** `DOCUMENTDB_URI` (SCRAM-SHA-256, `tls=true`) is the fastest path to a running sample. It is the cluster admin credential; do not ship it to production.
- **Use Microsoft Entra ID in production.** Enable `MicrosoftEntraID` on the cluster, register the app's managed identity, and connect with `authMechanism=MONGODB-OIDC` (see `src/db.*` for the commented OIDC path). No password to store or rotate.
- **Least privilege if you must use a password.** Create a secondary native user (read-only `readAnyDatabase`, or a database-scoped custom role) with `mongosh` as the admin; the app never uses the admin user.
- **Secrets.** Keep `DOCUMENTDB_URI` / model keys in Azure Key Vault and reference them from App Service / Container Apps / Functions settings; `.env` is for local development only and is gitignored.
- **Network.** Restrict the cluster firewall to known IPs or use a Private Endpoint and disable public access.
- **TLS.** The app refuses URIs without `tls=true` or with `tlsAllowInvalidCertificates`.
- **Diagnostics.** Enable diagnostic settings and slow-query logs to Log Analytics (see the `documentdb-monitoring` skill).
- **Local development.** `ghcr.io/documentdb/documentdb/documentdb-local` on port 10260 with `--tlsAllowInvalidCertificates` is acceptable only locally.
```

### 4. New rule `skills/security/security-redact-logs.md`

Cross-link from `security-tls-required.md` to the guard in step 2 so the rule has runnable code. Incorrect: `console.error(err)`, `logger.error(payload)`, printing the connection error object at startup. Correct: the `logError`/`redact` helper above, Python equivalent with `logging` and `type(err).__name__`.

### 5. Wire-up

Add both rules to `skills/security/SKILL.md`, mention them in `docs/SKILLS.md`, and add one line to `skills/connection/SKILL.md` "When Creating Code": "Every generated app that reads `DOCUMENTDB_URI` must call the TLS guard, use the redacting logger, and include the README block from `security-sample-readme-production-notes`."

## Evidence (run folders under `runs/`)

- `runs/14-customer-complaint-classifier/20261124-201931/decisions.jsonl` (D005, D011: Entra skipped as "complex OIDC setup") and `05-audit.json`
- `runs/03-medication-interaction-checker/20261124-193347/05-audit.json` (P04 Entra violated, P20 `console.error(err)` with PHI/prompts)
- `runs/17-seasonal-trend-spotter-agent/20261124-185115/05-audit.json` (P02 TLS, P16 least privilege, P19 local gateway; cites the kit's own skills as the violated source)
- `runs/06-omnichannel-interaction-history/20261124-204007/05-audit.json` (P25 full error printed on connect failure, no minimal-error handler)
- `runs/04-earnings-call-rag-assistant/20261124-190247/05-audit.json` (no `tls=true` check, no least-privilege user)
- `runs/06-collateral-management-store/20261124-200922/02-readiness.json` (cold answer: Entra ID "not supported" for the data plane)

## Verification

### 1. Already covered? partially_covered
- `skills/security/security-entra-rbac.md` exists and recommends Entra ID, but its "Correct" block is a placeholder: `authMechanism: "MONGODB-OIDC", // or the current documented mechanism` with `// credentialProvider: Azure Managed Identity` commented out and "(verify current driver support/spec in the official docs)". Its Incorrect example uses host `prod-ddb.mongocluster.documentdb.azure.com`, and its SCRAM example uses `{ role: "readWrite", db: "orders" }`.
- `skills/connection/SKILL.md` line 70-74 "Authentication": "Default mechanism: `SCRAM-SHA-256`" only; no OIDC.
- Partly covered elsewhere: `skills/security/security-tls-required.md` (Incorrect: `tlsAllowInvalidCertificates: true`), `skills/security/security-private-endpoint.md` (Private Endpoint, disable public access), `skills/local-deployment/local-env-driven-config.md` ("Never default `tlsAllowInvalidCertificates` to `true`"). No URI-validation helper, no redacting logger, no README production-notes block, no Key Vault app-secret guidance (Key Vault appears only in `security-cmk-encryption.md` for CMK). grep for `redact` hits only `natural-language-querying` (query-result redaction, not logging).
- documentdb-mcp is not the target; Learn already has working OIDC code (below), so the gap is the kit, not Learn.

### 2. Premise true? confirmed (with corrections applied)
- Learn https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (updated 2026-11-23): `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`; `az documentdb mongocluster microsoft-entra-user assign --object-id ... --cluster-name ... --resource-group ... --type User --role db=admin role=root`; use the object ID, "not the application/client ID"; Python `AzureIdentityTokenCallback(OIDCCallback)` with scope `https://ossrdbms-aad.database.windows.net/.default`, `authMechanism="MONGODB-OIDC"`; TypeScript with `OIDC_CALLBACK` and `ALLOWED_HOSTS: ['*.azure.com']`; host `*.mongocluster.cosmos.azure.com` / `*.global.mongocluster.cosmos.azure.com`. Draft code matches. The Learn TS sample computes `expiresOnTimestamp - Date.now()/1000` (ms minus s); the draft's divide-by-1000 is correct, and a note was added.
- Kit host suffix `.mongocluster.documentdb.azure.com` is wrong; correct is `.mongocluster.cosmos.azure.com` (Learn connection parameters table). Confirmed.
- Learn https://learn.microsoft.com/en-us/azure/documentdb/secondary-users (updated 2026-11-17): native roles `readWriteAnyDatabase`, `clusterAdmin`, `readAnyDatabase`; "Manage users and roles by using interactive Mongo Shell (`mongosh`). ARM REST APIs, ARM-based Azure CLI commands, Bicep, and Terraform don't support secondary-user role assignments."; database- and collection-scoped custom roles with actions find/insert/update/delete (preview). A db-scoped built-in `readWrite` is not listed, so the kit example is unsupported. Correction applied: the draft said read-write requires `readWriteAnyDatabase` + `clusterAdmin` together; the current secondary-users page lists them as separate roles (with a `validate ... repair` caveat for `readWriteAnyDatabase`), while the Entra page still requires the pair for nonadministrative Entra identities. The body now states both.
- D005/D011 in `runs/14-customer-complaint-classifier/20261124-201931/decisions.jsonl` exist; recorded reasons are "avoids complex OIDC setup" and "would add complexity and extra secrets management", with `reason_source: prompt`. Wording corrected: the harness-supplied URI was the main driver, not only the missing example.
- Sample/finding counts (23 samples, 35 findings) taken from the theme cluster; 35 finding ids listed below.

### 3. Maintainer skeptic: confirmed
Names exact files (`skills/security/security-entra-rbac.md`, `skills/connection/SKILL.md`, `skills/security/SKILL.md`, `docs/SKILLS.md`, two new rule files), fixes two factual errors in an existing rule (host suffix, unsupported role) and replaces a non-runnable placeholder with Learn-verified code. The README block and redacting logger are generic hygiene on their own, but they are tied to DocumentDB specifics (admin SCRAM URI, Entra/MONGODB-OIDC, secondary users via mongosh, local gateway on 10260) and fit the kit's rule format. Acceptable as one PR; a maintainer might ask to split the Entra-rule fix (highest value) from the new rules.

## Finding ids

- F0028
- F0140
- F0248
- F0303
- F0240
- F0408
- F0583
- F0582
- F0416
- F0747
- F0874
- F0691
- F0756
- F0883
- F0993
- F0992
- F0938
- F0911
- F1322
- F1324
- F1329
- F1395
- F1514
- F1515
- F1780
- F1945
- F2045
- F2180
- F2349
- F2931
- F2932
- F2933
- F3061
- F3519
- F3527
