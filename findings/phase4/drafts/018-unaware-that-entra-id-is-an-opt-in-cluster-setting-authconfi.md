---
title: "Agent Kit: document that Entra ID is an opt-in cluster auth mode (authConfig.allowedModes) and that principals must be registered as cluster users, not granted via keys or Azure RBAC"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 17
findings: 17
bucket: confusion-Q06
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Document Entra ID as an opt-in cluster auth mode and show how a principal becomes a cluster user (no account keys, not Azure RBAC on the data plane)

## What happens today

The kit tells agents to "prefer Entra when available" but never shows the two things an agent has to do to make that true on an Azure DocumentDB cluster:

1. **Turn the mode on.** `Microsoft.DocumentDB/mongoClusters` has `properties.authConfig.allowedModes` (`NativeAuth`, `MicrosoftEntraID`). A new cluster uses native authentication only by default; Entra is added with `az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID`, the portal, or Bicep/ARM. `skills/azure-deployment/SKILL.md` Step 9 ("configure access") just says *"Entra RBAC / CMK / diagnostic settings. See `documentdb-security`"*, and neither `references/bicep-cluster-template.md` nor `references/terraform-cluster-template.md` mentions `authConfig`.
2. **Register the principal as a cluster user.** Data-plane authorization is the cluster's MongoDB role set on a registered user: administrators via the ARM `Microsoft.DocumentDB/mongoClusters/users` sub-resource (or `az documentdb mongocluster microsoft-entra-user assign`), with `identityProvider.type: MicrosoftEntraID` and `principalType: user | servicePrincipal` and role `root` on `admin`; nonadministrative users via the MongoDB `createUser` command with `customData.IdentityProvider` (the ARM users endpoint supports administrative registration only). `skills/security/security-entra-rbac.md` shows an OIDC `MongoClient` snippet with the comment *"or the current documented mechanism"* and a SCRAM `createUser` example, but no enable step, no registration step, and no statement that there are **no account keys** and that an Azure role assignment on the resource does **not** grant data access.
3. `skills/mcp-setup/SKILL.md` only uses `authMode: "entra"` as a `CONNECTION_PROFILES` value and, under "Auth errors", says to check "Settings → Authentication" without saying what to look for.

## Why it matters

In a 100-sample readiness run with gpt-5-mini, the cold-quiz question *"Which authentication methods are supported, and how does a driver authenticate with Microsoft Entra ID?"* was wrong or partly wrong in **17 samples** for this reason:

- **15 samples** said Entra ID is not available on the MongoDB wire protocol / "drivers normally connect with SCRAM" (the Cosmos DB for MongoDB RU prior), or, the other way round, assumed it works without enabling anything on the cluster.
- **2 samples** described the Cosmos DB for NoSQL model instead: data-plane auth with account primary keys, or Entra access granted through Azure RBAC role assignments on the account.

Downstream, those builds defaulted to a password connection string and either did not mention Entra or could not say why (the audit for `16-population-health-dashboard-backend` flags "does not implement Microsoft Entra ID (MONGODB-OIDC) nor document why not"). The Learn RBAC page already documents the enable step, user registration and the role table, so the missing piece is the kit.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md` (Step 9) and the Bicep/Terraform references

Replace the one-line Step 9 pointer with:

```markdown
- **Microsoft Entra ID auth** (recommended for prod). New clusters use native auth only.
  Entra stays off until `authConfig.allowedModes` includes `MicrosoftEntraID`. Keep
  `NativeAuth` until an Entra principal has connected successfully:
  ```bash
  az documentdb mongocluster update \
    --name <cluster-name> --resource-group <resource-group> \
    --auth-allowed-modes NativeAuth MicrosoftEntraID
  az resource show --resource-type Microsoft.DocumentDB/mongoClusters \
    --name <cluster-name> --resource-group <resource-group> \
    --query properties.authConfig
  ```
  Enabling the mode grants nobody access. Each identity must then be registered as a
  cluster user (see `documentdb-security` -> security-entra-rbac). Azure role
  assignments (Contributor, Owner, custom roles with
  `Microsoft.DocumentDB/mongoClusters/users/write`) only control who may manage the
  cluster and its user registrations; they never let a driver connect.
```

In `references/bicep-cluster-template.md` add a param and property:

```bicep
@description('Allowed authentication modes. Add MicrosoftEntraID to enable Entra ID auth.')
param authAllowedModes array = ['NativeAuth']
...
  properties: {
    administrator: { ... }
    authConfig: { allowedModes: authAllowedModes }
```

add the equivalent `authConfig` block to the Terraform template, and add `"authConfig": { "allowedModes": ["NativeAuth"] }` to the `az resource create --properties` JSON in Step 6b with a comment on adding `MicrosoftEntraID`.

### 2. `skills/security/security-entra-rbac.md`

Add this block between "Why it matters" and "Incorrect":

```markdown
## How authorization works on Azure DocumentDB (read before coding)

- **There are no account keys.** Native auth is a SCRAM user + password. Cosmos DB
  "primary key" / "resource token" auth does not exist here.
- **Entra ID is opt-in per cluster.** `authConfig.allowedModes` must contain
  `MicrosoftEntraID` (`az documentdb mongocluster update --auth-allowed-modes NativeAuth MicrosoftEntraID`).
- **Data access comes from MongoDB roles on a registered principal, not an Azure role
  assignment.** Azure RBAC on the `mongoClusters` resource is control plane only (who
  can manage the cluster and register users). Each managed identity, service principal
  or user must be registered inside the cluster:

  *Administrator* (`root` on `admin`): Azure CLI
  `az documentdb mongocluster microsoft-entra-user assign --object-id <object-id> --cluster-name <cluster> --resource-group <rg> --type User --role db=admin role=root`
  (use the service-principal type for a managed identity), or the ARM
  `Microsoft.DocumentDB/mongoClusters/users` resource (name = principal object ID):
  ```json
  { "properties": {
      "identityProvider": { "type": "MicrosoftEntraID", "properties": { "principalType": "servicePrincipal" } },
      "roles": [ { "db": "admin", "role": "root" } ] } }
  ```
  *Nonadministrative*: sign in as an Entra administrator and run `createUser` (the ARM
  users endpoint supports administrative registration only; do not register the
  principal through ARM first):
  ```javascript
  db.getSiblingDB("admin").runCommand({
    createUser: "<principal-object-id>",
    roles: [ { role: "clusterAdmin", db: "admin" }, { role: "readWriteAnyDatabase", db: "admin" } ], // read-write pair; or [{ role: "readAnyDatabase", db: "admin" }] for read-only
    customData: { IdentityProvider: { type: "MicrosoftEntraID", properties: { principalType: "servicePrincipal" } } }
  })
  ```
  Verify with `db.getSiblingDB("admin").runCommand({ usersInfo: 1 })`; ARM user
  listings do not show these database-only users.
```

Replace the hedged `MongoClient` snippet in "Correct" with the documented callback form (`authMechanism: "MONGODB-OIDC"` plus an OIDC callback that calls `DefaultAzureCredential().getToken("https://ossrdbms-aad.database.windows.net/.default")`, as in the Learn page's TypeScript/Python examples) and drop the comment *"or the current documented mechanism"*.

### 3. `skills/mcp-setup/SKILL.md`

Before the `CONNECTION_PROFILES` example in Step 4:

```markdown
Pick `authMode` from the cluster, not from habit: run
`az resource show --resource-type Microsoft.DocumentDB/mongoClusters -n <cluster> -g <rg> --query properties.authConfig.allowedModes`.
Use `"authMode": "entra"` only if the list contains `MicrosoftEntraID` **and** the identity
running the MCP server is registered as a cluster user; otherwise use `connectionString`.
```

and extend the "Auth errors" troubleshooting bullet with: *"for Entra, confirm `MicrosoftEntraID` is in `allowedModes` and the principal appears in `usersInfo` (or in the cluster's Entra user list for administrators)."*

## Evidence (run folders from the readiness experiment)

- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json`: confusions[Q06], cold answer described account primary/secondary keys and said Entra ID is not generally available; 05-audit.json doc_gaps "Entra ID auth example for Python apps".
- `runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json`: confusions[Q06], credentials mapped to account keys, resource tokens and Azure RBAC (NoSQL model).
- `runs/14-telehealth-session-summarizer/20261124-195137/02-readiness.json`: confusions[Q06], "direct driver auth with Azure AD tokens is not generally supported".
- `runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json`: requirement "Use Microsoft Entra ID" not met and not explained.
- `runs/17-rare-disease-literature-search/20261124-195633/02-readiness.json`: confusions[Q06], build_risk names both failure modes (assume impossible / assume on by default).

Source for the facts above: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (sections "Enable Microsoft Entra ID authentication", administrative and nonadministrative identity management, connection examples).

## Verification

### 1. Already covered? confirmed (not in the target)

- Grep of `skills/` and `knowledge-base/` in the Agent Kit clone for `authConfig`, `allowed-modes`, `allowedModes`, `MicrosoftEntraID`, `IdentityProvider`, `mongoClusters/users`, `account key` returned no hits (only an unrelated `az role assignment list` preflight in `skills/azure-deployment/SKILL.md:39`).
- `skills/azure-deployment/SKILL.md:311`: "**Entra RBAC / CMK / diagnostic settings**. See `documentdb-security` and `documentdb-monitoring`." No enable step.
- `skills/security/security-entra-rbac.md:26`: `authMechanism: "MONGODB-OIDC", // or the current documented mechanism`; no enable or registration step; only a SCRAM `createUser` example.
- `skills/mcp-setup/SKILL.md:214-215`: "verify the database user exists in Azure portal under your cluster's Settings → Authentication, and that the password is correct." Nothing on allowedModes.
- microsoft/documentdb-mcp only supports `authMode=entra` profiles (README, tool_list.md); it does not and should not document cluster-side enablement, so no overlap.
- Learn already covers it fully (the RBAC page below), confirming the gap is kit-only, as the draft says.

### 2. Premise true? confirmed (with precision edits applied)

Checked against https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (updated 2026-11-23):
- "When you create an Azure DocumentDB cluster, the cluster is configured to solely use native authentication by default." Enable with `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`; Bicep/ARM `authConfig.allowedModes`.
- Administrators: `Microsoft.DocumentDB/mongoClusters/users` with `identityProvider` / `principalType` and role `root`; also `az documentdb mongocluster microsoft-entra-user assign`. "The ARM `Microsoft.DocumentDB/mongoClusters/users` endpoint supports administrative registration only."
- Nonadministrative: `createUser` with `customData.IdentityProvider.type: MicrosoftEntraID`; roles `readWriteAnyDatabase` + `clusterAdmin` together, or `readAnyDatabase`.
- OIDC: `authMechanism=MONGODB-OIDC`, token scope `https://ossrdbms-aad.database.windows.net/.default`, `DefaultAzureCredential`.
Edits applied to the body: (a) added the `az documentdb mongocluster microsoft-entra-user assign` CLI route the Learn page documents for admin registration; (b) qualified "not Azure RBAC" — the Learn page does use Azure role definitions/assignments for the control plane (including `mongoClusters/users/write`), so the text now says Azure RBAC is control-plane only and never grants data access; (c) clarified the read-write pair vs read-only alternative and that ARM listings do not show database-only users; (d) added the token scope to the OIDC snippet guidance; (e) removed the Bicep `@allowed` decorator, which is not valid on an array param in the way drafted; (f) used the generic `az resource show` verification shown on Learn; (g) added the Terraform template, which also lacks `authConfig`.

### 3. Maintainer skeptic: confirmed

Names three specific files and their exact sections (azure-deployment Step 9 and Step 6b plus bicep/terraform references, security-entra-rbac.md, mcp-setup Step 4 and Troubleshooting), gives drop-in text, is specific to Azure DocumentDB's mongoClusters auth model, and replaces a hedge ("or the current documented mechanism") the kit itself flags as unverified. As a kit maintainer I would accept it as a PR with the edits above.

## Finding ids

F1558, F1657, F1790, F1952, F1983, F2186, F2359, F2460, F2684, F2713, F2747, F2779, F2806, F2876, F3014, F1299, F0889
