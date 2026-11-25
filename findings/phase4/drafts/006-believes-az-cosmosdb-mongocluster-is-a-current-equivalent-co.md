---
title: "Learn: mark `az cosmosdb mongocluster` as superseded by `az documentdb mongocluster` and cross-link the two CLI references"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 3
findings: 3
bucket: confusion-Q02
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Mark `az cosmosdb mongocluster` as superseded by `az documentdb mongocluster` and cross-link the CLI references

## What happens today

Three Learn pages are involved. Only one of them shows which CLI group Azure DocumentDB uses, and none of them says how the two groups relate:

- https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster is still live. Its only notes say it belongs to the `cosmosdb-preview` extension (CLI 2.17.1 or higher) and that the group "is in preview and under development". Every command is marked Preview, none is marked Deprecated. The page never mentions `az documentdb mongocluster` or Azure DocumentDB, and never says this surface dates from the "Azure Cosmos DB for MongoDB vCore" era. (Checked 2026-11-25.)
- https://learn.microsoft.com/cli/azure/documentdb/mongocluster (the `documentdb` extension, CLI 2.75.0 or higher) is the group the Azure DocumentDB docs use. It is also marked Preview ("Command group 'az documentdb' is in preview and under development") and never mentions the older `az cosmosdb mongocluster` group.
- https://learn.microsoft.com/azure/documentdb/quickstart-cli already installs the right extension (`az extension add --name documentdb --upgrade`) and uses `az documentdb mongocluster` for every step. It does not warn readers off `az cosmosdb mongocluster` or `az cosmosdb create --kind MongoDB`.

Both groups carry the same Preview status and neither page links to the other. When Learn search returns both reference pages for a query like "az cosmosdb mongoClusters ... azure documentdb cli create", nothing tells the reader which one is current. An agent that grounds on Learn concludes the two groups are aliases.

## Why it matters

In an experiment that ran a readiness quiz over 101 Azure DocumentDB sample prompts with gpt-5-mini, grounded on Learn search:

- 56 of 101 samples referenced https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster somewhere in their readiness output. For 25 of them it was a grounding link for the question "Which Azure CLI command group creates and manages a cluster?"
- 42 samples gave a grounded answer to that question that names `az cosmosdb mongocluster` as a current or alternative spelling of `az documentdb mongocluster`. Examples: "also surfaced under az cosmosdb mongocluster in some docs/CLI versions" and "az documentdb mongocluster (or az cosmosdb mongocluster) group is used to create/manage mongoClusters".
- In the 3 samples behind this issue, the model's own proposed fix was to document `az cosmosdb mongocluster create` on the Azure DocumentDB pages. The Learn results reinforced the wrong belief instead of correcting it.

Only 1 of 101 samples answered this question correctly. The builds in this experiment used a pre-provisioned cluster, so no run actually executed the legacy command. Any agent asked to provision a cluster from these pages, though, may pick the older `cosmosdb-preview` group, whose parameter surface is different (for example `--shard-node-tier` / `--administrator-login` instead of `--tier` / `--admin-user`). Or it may fall back to `az cosmosdb create --kind MongoDB`, the cold answer in all three samples, which creates an Azure Cosmos DB account (`Microsoft.DocumentDB/databaseAccounts`), not a `Microsoft.DocumentDB/mongoClusters` cluster.

The change must keep these facts intact:
- The Azure DocumentDB docs use the `az documentdb mongocluster` group, from the `documentdb` extension.
- The resource type is `Microsoft.DocumentDB/mongoClusters`.
- The service was formerly "Azure Cosmos DB for MongoDB vCore".
- Both CLI groups are currently in Preview. Neither page should imply that `az documentdb` is GA.

## Proposed change

1. **Legacy reference: https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster and its command pages.** Add a prominent note above the command table:
   > For Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`), use [az documentdb mongocluster](https://learn.microsoft.com/cli/azure/documentdb/mongocluster) (documentdb extension). The `az cosmosdb mongocluster` group comes from the earlier Azure Cosmos DB for MongoDB vCore preview and is superseded by `az documentdb mongocluster`.

   These reference pages are generated from extension help text (source: MicrosoftDocs/azure-docs-cli `docs-ref-autogen/.../cosmosdb/mongocluster.yml`). The durable way to add the note is in the `cosmosdb-preview` extension in Azure/azure-cli-extensions: set `deprecate_info` on the `cosmosdb mongocluster` command group with `redirect='documentdb mongocluster'`. Learn then shows a Deprecated status and the redirect text on every command page. The CLI or extension owners need to confirm the deprecation decision.

2. **Current reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster.** Add one sentence to the group's help summary, which currently reads "Manage Azure DocumentDB mongo clusters.":
   > This is the command group for Azure DocumentDB clusters. It supersedes the older `az cosmosdb mongocluster` group (cosmosdb-preview extension).

   This page is also generated, so the change belongs in the `documentdb` extension's help text in Azure/azure-cli-extensions.

3. **Quickstart: https://learn.microsoft.com/azure/documentdb/quickstart-cli, after the `az extension add --name documentdb --upgrade` step in Prerequisites.** The extension install is already there. Add only this note:
   > [!NOTE]
   > Azure DocumentDB clusters are managed with `az documentdb mongocluster`. Don't use `az cosmosdb mongocluster` (an older, superseded preview group) or `az cosmosdb create --kind MongoDB`, which creates an Azure Cosmos DB account instead of a DocumentDB cluster.

Item 3 is a plain Markdown edit in the Azure DocumentDB doc set (MicrosoftDocs/nosql-docs-pr, `azure/documentdb/quickstart-cli.md`). Items 1 and 2 need the azure-cli-extensions owners, because both reference pages are generated. Item 3 alone still gives Learn search one page that explicitly ranks the two groups, and that ranking is what the grounded agents were missing.

## Evidence (run folders, 02-readiness.json, Q02 confusions)

- runs/04-customer-journey-mapper/20261124-203553: the grounded answer says the current command surface includes `az cosmosdb mongocluster` commands, grounded on the legacy reference page. Its proposed improvement is a note on the mongoClusters page that "shows az cosmosdb mongocluster create".
- runs/06-collateral-management-store/20261124-200922: the grounded answer lists `az documentdb mongocluster` and `az cosmosdb mongocluster` together, with both reference pages as grounding links. In events.jsonl, the Learn search result for `az cosmosdb mongocluster create` comes back with "Preview" as its only status.
- runs/06-symptom-triage-chatbot-rag/20261124-193845: grounded answer: "az documentdb mongocluster (or az cosmosdb mongocluster)". Its proposed improvement is to document "az documentdb mongocluster create or az cosmosdb mongocluster create examples".
- runs/10-support-ticket-rag-assistant/20261124-204529: the readiness summary says "CLI groups include az documentdb / az cosmosdb mongocluster".
- runs/20-store-locator-with-geospatial-search/20261124-185729: the grounded answer is built on both CLI references. The proposed improvement is to clarify "az documentdb mongocluster or az cosmosdb mongocluster".

## Verification

### 1. Already covered? partially_covered

- https://learn.microsoft.com/azure/documentdb/quickstart-cli (checked 2026-11-25) already shows the correct path. Prerequisites include "Install or update the Azure DocumentDB extension for Azure CLI" with `az extension add --name documentdb --upgrade`, and every step uses `az documentdb mongocluster`. The original draft said the prerequisites never name the extension. That was wrong, and item 3 was cut down to the warning note.
- https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster has no deprecation or redirect notice. Its only note is: "This reference is part of the cosmosdb-preview extension ... This command group is in preview and under development." All 12 commands are listed as Preview. It does not mention `az documentdb`.
- https://learn.microsoft.com/cli/azure/documentdb/mongocluster has no cross-link to or mention of `az cosmosdb mongocluster`. The only "cosmosdb" text on the page is the `--network-bypass-mode AzureCosmosDB` value.
- Agent Kit and MCP: `grep -rniE 'az (documentdb|cosmosdb)|mongocluster '` over documentdb-agent-kit/skills, documentdb-agent-kit/knowledge-base and documentdb-mcp found one hit, skills/storage/storage-premium-ssdv2-limitations.md:28, `az documentdb mongo-cluster restore`. No guidance on the legacy group was found. That hit spells the group `mongo-cluster`, while Learn uses `mongocluster`; this belongs in a separate agent-kit issue.
- Conclusion: the correct group is documented, but nothing marks the legacy group as superseded or cross-links the two. That missing cross-link is the gap the grounded agents fell into.

### 2. Is the premise true? confirmed (with corrections applied)

- Confirmed: the legacy `az cosmosdb mongocluster` reference is live, comes from `cosmosdb-preview`, and has no deprecation or redirect (Learn page above; source mongocluster.yml in MicrosoftDocs/azure-docs-cli). Its parameters (`--shard-node-tier`, `--administrator-login`, `--server-version` default 5.0) differ from the `az documentdb mongocluster create` surface (`--tier`, `--admin-user`, `--server-version 8.0` in the quickstart).
- Confirmed: `az documentdb mongocluster` (documentdb extension, CLI 2.75.0 or higher) is the group the Azure DocumentDB quickstart uses. The resource type is `Microsoft.DocumentDB/mongoClusters`. `az cosmosdb create --kind MongoDB` creates a `databaseAccounts` resource.
- Corrected: the draft described the legacy group as "a preview extension that is no longer the supported path", which implied `az documentdb` is not preview. The Learn reference marks `az documentdb` as Preview too. The body now says both groups are Preview, and the proposed notes no longer call `az documentdb` the only "supported" group.
- Corrected: the draft said the legacy group "receives no new features". No source was found for that, so it was removed.
- Corrected statistics, recomputed from runs/*/*/02-readiness.json: 56 of 101 samples reference the legacy page anywhere in readiness output, but only 25 cite it as a Q02 grounding link (the draft said 56 for Q02). 42 samples' grounded Q02 answers name `az cosmosdb mongocluster`, and 1 sample's Q02 outcome is "correct". Both of those match the draft.
- Corrected: the draft said items 2 and 3 are plain Markdown edits. The `az documentdb mongocluster` reference is generated (docs-ref-autogen), so item 2 also needs an extension help-text change. Only item 3 is a Markdown edit.
- Verified against the run folders: in 06-collateral-management-store/20261124-200922/events.jsonl, the learn_microsoft_docs_search result for the legacy page shows "Preview" as its only status.

### 3. Maintainer skeptic: confirmed

The draft names exact pages, gives concrete replacement text, and has a clear Azure DocumentDB angle: the rename from Azure Cosmos DB for MongoDB vCore left two CLI groups live side by side. As a Learn maintainer I would accept item 3 as written in MicrosoftDocs/nosql-docs-pr (`azure/documentdb/quickstart-cli.md`). Items 1 and 2 change auto-generated CLI reference pages, so they have to land in Azure/azure-cli-extensions (`cosmosdb-preview` deprecate_info and `documentdb` group help). The body now says so. The repo stays learn-docs because the doc-set change is the primary fix and the reference pages are rendered on Learn.

## Finding ids

- F0522
- F0844
- F0966
