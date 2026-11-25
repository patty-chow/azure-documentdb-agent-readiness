---
id: K25
title: "Let the kit identify itself as installed (front-matter metadata and installer check)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 23
member_drafts:
  - 057-kit-cannot-tell-it-is-already-installed-add-an-install-verif.md
open_questions: 2
---

# Let the kit identify itself as installed (front-matter metadata and installer check)

## What happens today

An agent that has the kit's 17 skills on disk has no cheap way to tell whether the DocumentDB Agent Kit is installed, or which version:

- Installed skills are named `documentdb-<name>`, and nothing inside them says they come from `Azure/documentdb-agent-kit`. Their front matter has only `name` and `description`. The only attribution is in the skills.sh lock file (`skills-lock.json`), and agents do not read it.
- `AGENTS.md` (Route B, step 1) checks for `~/.agents/skills/find-skills/` but never checks for the kit itself. `skills/mcp-setup/SKILL.md` goes straight to "Fastest path: bundled installer" without looking for an existing install.
- `install.sh` and `install.ps1` log "Kit installed at: ..." but write no manifest or version marker. There is no root `VERSION` file. The four plugin manifests (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`) say `0.1.0`, while `CHANGELOG.md` has a "v0.2.0" heading. A skills-only install carries no version at all.
- `docs/installation/verify.md` checks only the MCP server, not the skills.
- The 2026-05-21 `CHANGELOG.md` entry contradicts itself. It opens by saying it replaced the "non-functional" `npx skills add Azure/documentdb-agent-kit` placeholder, and a later bullet in the same entry says the README now documents that one-liner for skills-only installs. `README.md`, `AGENTS.md`, `docs/installation/skills-only.md` and `docs/installation/updating.md` all present the command as the skills-only install and update path, and it works today. A reader who sees the "non-functional" wording first concludes the README is wrong.

## Why it matters

We ran an agent-readiness check over 100 Azure DocumentDB sample prompts (gpt-5-mini). All 17 kit skills were installed with `npx skills add` for every run. In 24 runs covering 23 distinct samples, the model still listed the kit as a *missing* accelerator and recommended installing it. In one run it said the individual DocumentDB skills were already installed and still recommended installing the kit. It saw `documentdb-indexing`, `documentdb-vector-search` and the rest but could not link them to "the kit". A user who followed that advice would rerun the installer over a working setup, or add a second copy of the skills through another install path.

Part of the cause is in our test harness, which should have told the model where the skills came from. That is being fixed separately. The kit's part is that nothing an agent can see marks an installed skill as belonging to the kit or says which version it is. Counts come from a single experiment run and include the harness effect, so they should be re-measured after the harness fix before being quoted outside this PR.

## Proposed change

**1. `skills/*/SKILL.md` (all 17): self-identifying front matter.** Add:

```yaml
metadata:
  kit: "documentdb-agent-kit"
  kit_version: "<x.y.z from VERSION>"
  kit_repo: "https://github.com/Azure/documentdb-agent-kit"
```

The Agent Skills format allows an optional `metadata` map of string keys to string values, so the values are quoted. Front matter is copied as-is by `npx skills add`, by the installer symlinks and by the plugin packages, so it is the one marker that survives every install path. Stamp `kit_version` from `VERSION` (small script or CI step) so the 17 copies cannot drift.

**2. New root `VERSION` file (one line), and the plugin manifests.** Settle on one number when this PR is cut (manifests say `0.1.0`, the CHANGELOG says `v0.2.0`). Stamp it into the four plugin manifests listed above.

**3. `install.sh` and `install.ps1`: write an install marker.** In `install.sh`, have `main()` write `~/.documentdb-agent-kit/kit.json` after the `install_skills_for_client` loop. Have `install.ps1` write the same file at the matching point:

```json
{"version":"<VERSION>","commit":"<git rev-parse HEAD in KIT_DIR>","installed_at":"<ISO-8601>","clients":["claude-code"],"skills_linked":17}
```

`--uninstall` / `-Uninstall` already removes `~/.documentdb-agent-kit`, so the marker goes with it and no new uninstall logic is needed. `--dry-run` / `-DryRun` should print the file instead of writing it.

**4. `AGENTS.md` (before Route B step 1) and `skills/mcp-setup/SKILL.md` (before "Fastest path: bundled installer"): add a step 0.**

> **0. Check whether the kit is already installed before suggesting any install command.** Look for `documentdb-*/SKILL.md` in the current agent's skills directory (`.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/`, or the client equivalent), or for `~/.documentdb-agent-kit/kit.json`. If either is found, read `metadata.kit_version` from any one `SKILL.md` (or `version` from `kit.json`), tell the user "DocumentDB Agent Kit <version> is installed", and offer only the matching **update** command from `docs/installation/updating.md`. If the skills are present but the DocumentDB MCP server is not, suggest `install.sh --mcp-only` / `install.ps1 -McpOnly`, not a full install. Only when neither is found, suggest `npx skills add Azure/documentdb-agent-kit` (skills only) or the installer one-liner (skills + MCP server).

**5. `CHANGELOG.md`.** Add a new dated entry saying that `npx skills add Azure/documentdb-agent-kit` is a supported skills-only install and update path, that the installers remain the path for skills + MCP server, and that plugin-marketplace installs are not yet published. Reword the opening sentence of the 2026-05-21 entry so it no longer calls the command "non-functional" (or append "(superseded, see <new entry>)").

**6. `README.md` "Installation".** Open with a three-row table: *Skills only* -> `npx skills add Azure/documentdb-agent-kit`; *Skills + MCP server* -> `install.sh` / `install.ps1`; *Plugin marketplaces* -> not yet published, see `docs/installation/plugin-marketplaces.md`. Add one sentence: the installers write `~/.documentdb-agent-kit/kit.json`, and every skill's front matter carries `metadata.kit_version`.

**7. `docs/installation/verify.md`.** Add step 0, "Verify the skills": run `ls ~/.claude/skills/documentdb-* | head` (or the client equivalent) and `cat ~/.documentdb-agent-kit/kit.json`. Expected: 17 directories and a version line.

**8. `docs/installation/skills-only.md` and `docs/installation/updating.md`.** Add one sentence to each: check `metadata.kit_version` in any installed `SKILL.md` to see which version is installed.

If reviewers prefer smaller PRs, items 5 to 8 (docs only) can be split out.

## Evidence

Run folders from the experiment; the readiness output is `02-readiness.json`, field `accelerators_missed`. In every run, `skills-lock.json` pinned all 17 skills to `Azure/documentdb-agent-kit` at commit `4f41c15`.

- `runs/07-lab-results-aggregator/20261124-194018/` (says the skills are installed, still lists the kit as missing)
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/`
- `runs/02-transaction-categorization-agent/20261124-190028/` (says the kit is "not present as a single npx package")
- `runs/09-trade-settlement-tracker/20261124-201323/`
- `runs/09-inventory-reorder-multi-agent-system/20261125-054042/` (repeat run, same result)

## Open questions

1. Which version number should `VERSION` start at: `0.1.0` (plugin manifests) or `0.2.0` (CHANGELOG heading)? Maintainers to decide.
2. Is `npx skills add Azure/documentdb-agent-kit` the intended long-term skills-only path? It works today, but the CHANGELOG once called it a non-functional placeholder; please confirm before the CHANGELOG wording is changed. Maintainers to decide.

No service-behavior claims in this PR needed SME confirmation. The harness-side fix (telling the checker the skills came from the kit) is tracked separately in the experiment harness.

## Source drafts

- 057-kit-cannot-tell-it-is-already-installed-add-an-install-verif.md
