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
open_questions: 2
---

# az cosmosdb mongocluster help text: mark it superseded by az documentdb mongocluster and cross-link the two reference pages

## What happens today

Two extension command groups manage the same Azure resource type, `Microsoft.DocumentDB/mongoClusters` (Azure DocumentDB, formerly Azure Cosmos DB for MongoDB vCore), and neither one's help text mentions the other:

- **`az cosmosdb mongocluster`** (`cosmosdb-preview` extension). The generated reference page, https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster, says only that the group belongs to `cosmosdb-preview` and "is in preview and under development". All 12 commands are marked Preview, none Deprecated. It never mentions `az documentdb mongocluster` or Azure DocumentDB. In the extension source, `setup_mongocluster_commands` registers `command_group('cosmosdb mongocluster', ..., is_preview=True)` with no `deprecate_info` (`src/cosmosdb-preview/azext_cosmosdb_preview/commands.py` lines 437-449), and `az cosmosdb mongocluster --help` (azure-cli 2.89.1, cosmosdb-preview 1.7.0) prints only the preview warning. The group's vendored SDK pins management API 2024-03-01-preview (`vendored_sdks/azure_mgmt_mongocluster/_configuration.py` line 37) and it has no list-connection-strings, restore, replica, identity or microsoft-entra-user commands.
- **`az documentdb mongocluster`** (`documentdb` extension, CLI 2.75.0 or higher). This is the group every Azure DocumentDB Learn page uses (for example https://learn.microsoft.com/azure/documentdb/quickstart-cli, how-to-scale-cluster, development-loop). Its group help reads only "Manage Azure DocumentDB mongo clusters." The reference page, https://learn.microsoft.com/cli/azure/documentdb/mongocluster, marks every command Preview because it is generated from the 1.1.0bX preview line of the extension; the version a fresh `az extension add --name documentdb` installs today (1.0.0) is a Stable release (Azure/azure-cli-extensions PR #10316, "Move DocumentDB extension to GA", merged 2026-09-16) and shows no preview banner. It never mentions the older group.

The parameter surfaces differ. The legacy `create` takes `--shard-node-tier`, `--administrator-login` and defaults `--server-version` to 5.0; the current one takes `--tier`, `--admin-user`, defaults to the latest server version, and the quickstart passes `--server-version 8.0`. Both pages show up in Learn search for "create an Azure DocumentDB cluster with the CLI", and nothing on either tells a reader which group is current. (Pages checked 2026-11-25.)

## Why it matters

We ran an AI-agent readiness experiment: 101 Azure DocumentDB sample apps, each with a quiz answered first from model memory and then grounded on Learn search (gpt-5-mini). All counts below come from that one experiment run (some samples ran more than once; a sample counts once), recounted from `runs/*/*/02-readiness.json`. The counts predate pending harness fixes and may shift on a re-run; see open question 2.

- For the question "Which Azure CLI command group creates and manages a cluster?", **42 of 101 samples** gave a grounded answer that names `az cosmosdb mongocluster` as a current or equivalent spelling of `az documentdb mongocluster` (for example, "az documentdb mongocluster (or az cosmosdb mongocluster)").
- 25 samples cited the `az cosmosdb mongocluster` reference page as a grounding link for that answer; 56 cited it somewhere in their output.
- Only 1 sample answered the question correctly.
- 13 samples went further: their proposed doc improvements for this question ask the docs to show `az cosmosdb mongocluster` as an alias or alternative to `az documentdb mongocluster`, and 5 of them name `az cosmosdb mongocluster create` explicitly. Grounding on the reference docs reinforced the wrong belief instead of correcting it.

The builds used a pre-provisioned cluster, so no run executed the legacy command. But an agent asked to provision a cluster from these pages can pick the older group, with its different parameters and older API version, or fall back to `az cosmosdb create --kind MongoDB` (the cold, ungrounded answer in the 3 samples behind the source draft), which creates a `databaseAccounts` resource rather than a `mongoClusters` cluster.

## Proposed change

Both reference pages are generated from extension help text, so the fix belongs in this repository.

1. **`cosmosdb-preview` extension, `cosmosdb mongocluster` command group.** Set `deprecate_info=self.deprecate(redirect='documentdb mongocluster')` on the group (the extension already uses this pattern: `cosmosdb dts` on `commands.py` line 300 carries `deprecate_info=self.deprecate(redirect='cosmosdb copy', hide=True)`), so the CLI warns at run time and Learn shows a Deprecated status and the redirect on every command page. If the owners do not want to deprecate yet (open question 1), fall back to a cross-link: add to the group's long-summary
   > For Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`), use `az documentdb mongocluster` (documentdb extension). This group comes from the earlier Azure Cosmos DB for MongoDB vCore preview and is superseded by `az documentdb mongocluster`.

   The word "superseded" is supported by the sources: every Learn DocumentDB page uses `az documentdb mongocluster`, and the legacy group is pinned to API 2024-03-01-preview and lacks the newer commands. The help text must not call the group "deprecated" unless the `deprecate_info` path is taken, because today it carries no deprecation marker.

2. **`documentdb` extension, `documentdb mongocluster` group help.** Extend the summary "Manage Azure DocumentDB mongo clusters." with:
   > This is the command group for Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`). It supersedes the older `az cosmosdb mongocluster` group in the cosmosdb-preview extension.

3. **`az documentdb mongocluster` reference page (https://learn.microsoft.com/cli/azure/documentdb/mongocluster).** The page shows every command as Preview because it is generated from the 1.1.0bX preview line, while `az extension add --name documentdb` installs stable 1.0.0 with no preview banner. Add a note on which extension version the page documents, and cross-link the legacy group. (The fix is in this repository's `src/documentdb` help text and release metadata; PR #10605, open 2026-11-20, proposes releasing 1.1.0 as Stable, which would remove the Preview status from the page.)

Constraints for the wording: describe `az cosmosdb mongocluster` as Preview (Learn reference and `is_preview=True` in source). Do not describe `az documentdb mongocluster` as unconditionally GA or unconditionally Preview: say "the reference page currently shows Preview"; the extension version installed by default (1.0.0) is Stable, only the 1.1.0bX line and the generated Learn page are Preview, and PR #10605 proposes a stable 1.1.0. Do not imply that `az cosmosdb create` manages mongoClusters. A separate Learn doc-feedback item asks for a matching note in the Azure DocumentDB CLI quickstart and product-overview pages.

## Evidence

Run folders in the experiment repository (file `02-readiness.json`, question Q02):

- runs/04-customer-journey-mapper/20261124-203553: grounded answer says the current surface includes `az cosmosdb mongocluster create`, grounded on the legacy reference page; proposes documenting that command.
- runs/06-collateral-management-store/20261124-200922: lists both groups together; in `events.jsonl` the Learn search result for the legacy page shows "Preview" as its only status.
- runs/06-symptom-triage-chatbot-rag/20261124-193845: "az documentdb mongocluster (or az cosmosdb mongocluster)".
- runs/10-support-ticket-rag-assistant/20261124-204529: summary says "CLI groups include az documentdb / az cosmosdb mongocluster".
- runs/20-store-locator-with-geospatial-search/20261124-185729: grounded on both references; proposes clarifying "az documentdb mongocluster or az cosmosdb mongocluster".

## Resolved

- Is `az cosmosdb mongocluster` deprecated or superseded? Not deprecated (live Preview group, `is_preview=True`, no `deprecate_info`, all 12 commands Preview on Learn), but superseded in practice: every Learn DocumentDB page uses `az documentdb mongocluster`, and the legacy group pins API 2024-03-01-preview and lacks list-connection-strings, restore, replica, identity and microsoft-entra-user. Sources: https://learn.microsoft.com/en-us/cli/azure/cosmosdb/mongocluster?view=azure-cli-latest; https://github.com/Azure/azure-cli-extensions/blob/main/src/cosmosdb-preview/azext_cosmosdb_preview/commands.py (lines 300, 437-449); https://github.com/Azure/azure-cli-extensions/blob/main/src/cosmosdb-preview/azext_cosmosdb_preview/vendored_sdks/azure_mgmt_mongocluster/_configuration.py (line 37); https://learn.microsoft.com/en-us/azure/documentdb/quickstart-cli (DECISIONS.md, SME topic 11).
- Release status of both groups. `az cosmosdb mongocluster` is Preview; for `az documentdb mongocluster` the Learn reference shows Preview because it is generated from the 1.1.0bX preview line, while the default-installed extension 1.0.0 is Stable (PR #10316, merged 2026-09-16) and PR #10605 proposes a stable 1.1.0, so filings say "the reference page currently shows Preview" and never "unconditionally GA" or "unconditionally Preview". Sources: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster?view=azure-cli-latest; https://github.com/Azure/azure-cli-extensions/blob/main/src/documentdb/HISTORY.rst; https://github.com/Azure/azure-cli-extensions/pull/10316; https://github.com/Azure/azure-cli-extensions/pull/10605; https://github.com/Azure/azure-cli-extensions/blob/main/src/documentdb/azext_documentdb/azext_metadata.json; https://aka.ms/azure-cli-extension-index-v1; local observation 2026-11-25 (az 2.89.1, `az extension list`, `az extension list-available`) (DECISIONS.md, SME topic 11).
- Can clusters created with `az cosmosdb mongocluster` be managed with `az documentdb mongocluster`? Yes by definition: both groups are thin clients over the same ARM resource type `Microsoft.DocumentDB/mongoClusters` and the same URL template (legacy at API 2024-03-01-preview, documentdb at 2026-06-15-preview), and the FAQ says the rename did not change existing clusters, connection strings or APIs; phrase it as "same resource type, same control plane" rather than quoting a doc, since no Learn page states cross-group compatibility in so many words. Sources: https://github.com/Azure/azure-cli-extensions/blob/main/src/cosmosdb-preview/azext_cosmosdb_preview/commands.py (lines 427-449); https://github.com/Azure/azure-cli-extensions/blob/main/src/documentdb/azext_documentdb/aaz/latest/documentdb/mongocluster/_show.py (lines 26-28); https://learn.microsoft.com/en-us/azure/documentdb/faq (DECISIONS.md, SME topic 11).
- Is there a source that the legacy group no longer receives fixes or features? No: no issue or PR in Azure/azure-cli-extensions mentions deprecating or redirecting the group, and cosmosdb-preview HISTORY.rst mentions it only at 0.24.0, so this issue does not assert it and relies only on the documented lag (API 2024-03-01-preview pin, missing newer commands). Sources: https://github.com/Azure/azure-cli-extensions/blob/main/src/cosmosdb-preview/azext_cosmosdb_preview/commands.py (lines 437-449); cosmosdb-preview HISTORY.rst; gh issue/PR search for "mongocluster" (DECISIONS.md, SME topic 11, open item 1).

## Open questions

1. [needs SME confirmation] Do the cosmosdb-preview owners plan to mark `az cosmosdb mongocluster` deprecated with a redirect to `az documentdb mongocluster`, and when? No issue or PR mentions it. This filing proposes `deprecate_info=self.deprecate(redirect='documentdb mongocluster')` on the group and falls back to a cross-link in both groups' help text; it keeps the word "superseded" and does not use "deprecated".
2. The sample counts (42, 56, 25, 13, 1 of 101) come from one run made before the pending harness fixes (MCP flags, accelerator detection, empty builds) and must be re-derived with a stated pattern before quoting them externally. Note that DECISIONS.md's topic-11 recount over `runs/*/events.jsonl` (fixed-string grep, 106 run folders) found `az cosmosdb mongocluster create` in 23 folders, `az documentdb mongocluster` in 79, and the legacy reference URL path `cli/azure/cosmosdb/mongocluster` in only 1, so the 25 and 56 citation counts from `02-readiness.json` need the same treatment before filing. Internal check, not an SME question.

## Source drafts

- 006-believes-az-cosmosdb-mongocluster-is-a-current-equivalent-co.md

## Finding ids

- F0522
- F0844
- F0966
