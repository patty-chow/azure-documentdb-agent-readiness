---
id: X01
title: "az cosmosdb mongocluster help text: mark it superseded by az documentdb mongocluster and cross-link the two reference pages"
repo: Azure/azure-cli-extensions
type: issue
status: needs_sme
priority: P1
sample_count: 42
member_drafts:
  - 006-believes-az-cosmosdb-mongocluster-is-a-current-equivalent-co.md
open_questions: 5
---

# az cosmosdb mongocluster help text: mark it superseded by az documentdb mongocluster and cross-link the two reference pages

## What happens today

Two extension command groups manage the same Azure resource type, `Microsoft.DocumentDB/mongoClusters` (Azure DocumentDB, formerly Azure Cosmos DB for MongoDB vCore), and neither one's help text mentions the other:

- **`az cosmosdb mongocluster`** (`cosmosdb-preview` extension). The generated reference page, https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster, says only that the group belongs to `cosmosdb-preview` and "is in preview and under development". All 12 commands are marked Preview, none Deprecated. It never mentions `az documentdb mongocluster` or Azure DocumentDB.
- **`az documentdb mongocluster`** (`documentdb` extension, CLI 2.75.0 or higher). This is the group the Azure DocumentDB documentation uses (for example https://learn.microsoft.com/azure/documentdb/quickstart-cli). Its group help reads only "Manage Azure DocumentDB mongo clusters." and it is also marked Preview. It never mentions the older group.

The parameter surfaces differ. The legacy `create` takes `--shard-node-tier`, `--administrator-login` and defaults `--server-version` to 5.0; the current one takes `--tier`, `--admin-user` and the quickstart uses `--server-version 8.0`. Both pages show up in Learn search for "create an Azure DocumentDB cluster with the CLI", and nothing on either tells a reader which group is current. (Pages checked 2026-11-25.)

## Why it matters

We ran an AI-agent readiness experiment: 101 Azure DocumentDB sample apps, each with a quiz answered first from model memory and then grounded on Learn search (gpt-5-mini). All counts below come from that one experiment run (some samples ran more than once; a sample counts once), recounted from `runs/*/*/02-readiness.json`. [needs SME confirmation] The counts predate pending harness fixes and may shift on a re-run; see open question 5.

- For the question "Which Azure CLI command group creates and manages a cluster?", **42 of 101 samples** gave a grounded answer that names `az cosmosdb mongocluster` as a current or equivalent spelling of `az documentdb mongocluster` (for example, "az documentdb mongocluster (or az cosmosdb mongocluster)").
- 25 samples cited the `az cosmosdb mongocluster` reference page as a grounding link for that answer; 56 cited it somewhere in their output.
- Only 1 sample answered the question correctly.
- 13 samples went further: their proposed doc improvements for this question ask the docs to show `az cosmosdb mongocluster` as an alias or alternative to `az documentdb mongocluster`, and 5 of them name `az cosmosdb mongocluster create` explicitly. Grounding on the reference docs reinforced the wrong belief instead of correcting it.

The builds used a pre-provisioned cluster, so no run executed the legacy command. But an agent asked to provision a cluster from these pages can pick the older group, with its different parameters, or fall back to `az cosmosdb create --kind MongoDB` (the cold, ungrounded answer in the 3 samples behind the source draft), which creates a `databaseAccounts` resource rather than a `mongoClusters` cluster.

## Proposed change

Both reference pages are generated from extension help text, so the fix belongs in this repository.

1. **`cosmosdb-preview` extension, `cosmosdb mongocluster` command group.** If the owners agree the group is superseded, set `deprecate_info` on the group with `redirect='documentdb mongocluster'`, so the CLI warns at run time and Learn shows a Deprecated status and the redirect on every command page. At minimum, add to the group's long-summary:
   > For Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`), use `az documentdb mongocluster` (documentdb extension). This group comes from the earlier Azure Cosmos DB for MongoDB vCore preview and is superseded by `az documentdb mongocluster`.

   [needs SME confirmation] The "superseded" wording in this note and the next depends on open question 1; if the owners only want a cross-link, drop that word and keep the pointer.

2. **`documentdb` extension, `documentdb mongocluster` group help.** Extend the summary "Manage Azure DocumentDB mongo clusters." with:
   > This is the command group for Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`). It supersedes the older `az cosmosdb mongocluster` group in the cosmosdb-preview extension.

Constraints for the wording: keep both groups described as Preview unless their status has changed (neither note should imply `az documentdb` is GA), and do not imply that `az cosmosdb create` manages mongoClusters. A separate Learn doc-feedback item asks for a matching note in the Azure DocumentDB CLI quickstart and product-overview pages.

## Evidence

Run folders in the experiment repository (file `02-readiness.json`, question Q02):

- runs/04-customer-journey-mapper/20261124-203553: grounded answer says the current surface includes `az cosmosdb mongocluster create`, grounded on the legacy reference page; proposes documenting that command.
- runs/06-collateral-management-store/20261124-200922: lists both groups together; in `events.jsonl` the Learn search result for the legacy page shows "Preview" as its only status.
- runs/06-symptom-triage-chatbot-rag/20261124-193845: "az documentdb mongocluster (or az cosmosdb mongocluster)".
- runs/10-support-ticket-rag-assistant/20261124-204529: summary says "CLI groups include az documentdb / az cosmosdb mongocluster".
- runs/20-store-locator-with-geospatial-search/20261124-185729: grounded on both references; proposes clarifying "az documentdb mongocluster or az cosmosdb mongocluster".

## Open questions

1. [needs SME confirmation] Is `az cosmosdb mongocluster` officially superseded by `az documentdb mongocluster`, and is deprecation (with a redirect) the owners' intended path, or should it only get a cross-link note?
2. [needs SME confirmation] Current release status of both groups: Learn marks both Preview. Confirm before either note states a status.
3. [needs SME confirmation] Can clusters created with `az cosmosdb mongocluster` be fully managed with `az documentdb mongocluster` (same resource type and API version), so the redirect is safe for existing users?
4. [needs SME confirmation] Is there any source for the legacy group no longer receiving fixes or features? An earlier draft claimed this; no source was found, so this issue does not assert it.
5. [needs SME confirmation] The sample counts (42, 56, 25, 13, 1 of 101) come from one run made before the pending harness fixes (MCP flags, accelerator detection, empty builds); the reviewer advises re-running before quoting counts externally. Confirm or refresh them before filing.

## Source drafts

- 006-believes-az-cosmosdb-mongocluster-is-a-current-equivalent-co.md

## Finding ids

- F0522
- F0844
- F0966
