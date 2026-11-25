---
title: "Kit cannot tell an agent it is already installed: add self-identification (front-matter metadata + installer marker), an \"am I installed?\" step in AGENTS.md/mcp-setup, and reconcile the npx install story"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 23
findings: 24
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Kit cannot tell an agent it is already installed: add self-identification, an "am I installed?" step, and reconcile the `npx skills add` story

## What happens today

An agent that has the kit's 17 skills on disk has no cheap way to answer "is the DocumentDB Agent Kit installed, and which version?":

- Installed skills are named `documentdb-<name>` and nothing inside them says they come from `Azure/documentdb-agent-kit`. Their front matter carries only `name` and `description`. The only attribution lives in the skills.sh lock file (`skills-lock.json`), which agents do not read.
- `AGENTS.md` (Route B, step 1) checks for `~/.agents/skills/find-skills/` but never for the kit itself.
- `install.sh` / `install.ps1` print "Kit installed at: ~/.documentdb-agent-kit/agent-kit" but write no manifest or version marker. The four plugin manifests (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`) say `0.1.0` (even though `CHANGELOG.md` has a "Retargeted to Azure DocumentDB (v0.2.0)" entry), and a skills-only install carries no version at all. There is no root `VERSION` file.
- `CHANGELOG.md` contradicts itself inside a single entry. The 2026-05-21 entry opens with "Replaced the non-functional `npx skills add Azure/documentdb-agent-kit` placeholder with real installers", and a bullet further down the same entry says the README "now documents the universal `npx skills add Azure/documentdb-agent-kit` one-liner (skills.sh) for skills-only installs". `README.md` line 131, `AGENTS.md` (per-agent install table), `docs/installation/skills-only.md` and `docs/installation/updating.md` all advertise that command as the skills-only install and update path. It works today: our runs installed commit `4f41c15` with it. The "non-functional" wording is stale, but a reader who sees it first concludes the README is wrong.

## Why it matters

We ran a readiness check over 100 Azure DocumentDB sample prompts with gpt-5-mini. All 17 kit skills were installed in `.agents/skills` for every run. In **24 runs (23 distinct samples)** the model still listed "DocumentDB Agent Kit (`npx skills add Azure/documentdb-agent-kit`)" as a *missing* accelerator and recommended installing it. In one run the model stated that the environment already had the individual DocumentDB skills installed and still recommended installing the kit. The model saw `documentdb-indexing`, `documentdb-vector-search` and the rest, and could not connect them to "the kit". A real user who followed that advice would re-run the installer over a working setup, or add a second copy of the skills through a different path.

Part of the cause is the harness: it should have told the checker that the skills came from the kit, and that is tracked separately. The kit's part is that nothing an agent can see marks an installed skill as kit-owned or says which version it is.

## Proposed change

**1. Self-identification in every skill (carried by every install path).** Add this to the YAML front matter of all 17 `skills/*/SKILL.md`:

```yaml
metadata:
  kit: "documentdb-agent-kit"
  kit_version: "<x.y.z from VERSION>"
  kit_repo: "https://github.com/Azure/documentdb-agent-kit"
```

The Agent Skills format allows an optional `metadata` map of string keys to string values, so quote the values. Front matter is copied verbatim by `npx skills add`, by the installer symlinks and by the plugin manifests, so it is the one place where a marker survives every install path. Pick the version number when the PR is cut (today the manifests say `0.1.0` and the CHANGELOG mentions `v0.2.0`, so settle on one), and stamp it from the `VERSION` file in step 2, either with a small script or in CI, so the 17 copies cannot drift.

**2. Version marker from the installers.** Add a root `VERSION` file (one line). Use it to stamp `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `gemini-extension.json` and the skill front matter. In `install.sh`, have `main()` write `~/.documentdb-agent-kit/kit.json` after the `install_skills_for_client` loop. Have `install.ps1` write the same file at the matching point:

```json
{"version":"<VERSION>","commit":"<git rev-parse HEAD in KIT_DIR>","installed_at":"<ISO-8601>","clients":["claude-code"],"skills_linked":17}
```

`--uninstall` / `-Uninstall` already removes `~/.documentdb-agent-kit`, which takes the file with it. `--dry-run` / `-DryRun` should print the file instead of writing it.

**3. "Step 0 - Am I installed?" in `AGENTS.md` and `skills/mcp-setup/SKILL.md`.** Insert it before Route B step 1 in `AGENTS.md` and before the "Fastest path: bundled installer" section in `skills/mcp-setup/SKILL.md`:

> **0. Check whether the kit is already installed before suggesting any install command.** Look for `documentdb-*/SKILL.md` in the current agent's skills directory (`.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/`, or the client equivalent), or for `~/.documentdb-agent-kit/kit.json`. If either is found, read `metadata.kit_version` from any one `SKILL.md` (or `version` from `kit.json`), tell the user "DocumentDB Agent Kit <version> is installed", and offer only the matching **update** command from `docs/installation/updating.md`. If the skills are present but the DocumentDB MCP server is not, suggest `install.sh --mcp-only` / `install.ps1 -McpOnly`, not a full install. Only when neither is found, suggest `npx skills add Azure/documentdb-agent-kit` (skills only) or the installer one-liner (skills + MCP server).

**4. Reconcile the install story.**
- `CHANGELOG.md`: add a new dated entry saying that `npx skills add Azure/documentdb-agent-kit` is a supported skills-only install and update path, that the installers remain the path for skills + MCP server, and that plugin-marketplace installs are still unpublished. Also reword the opening sentence of the 2026-05-21 entry so it no longer calls the command "non-functional" (or add "(superseded, see <new entry>)" after it), so the entry stops contradicting its own README bullet.
- `README.md` "Installation": open with a three-row table (*Skills only* -> `npx skills add ...`; *Skills + MCP server* -> `install.sh` / `install.ps1`; *Plugin marketplaces* -> not yet published, see `docs/installation/plugin-marketplaces.md`). State that the installers write `kit.json` and that every skill's front matter carries `metadata.kit_version`.
- `docs/installation/verify.md`: it currently checks only the MCP server. Add step 0, "Verify the skills": run `ls ~/.claude/skills/documentdb-* | head` (or the client equivalent) and `cat ~/.documentdb-agent-kit/kit.json`. Expected result: 17 directories and a version line.
- `docs/installation/skills-only.md` and `updating.md`: add one sentence to each pointing at the `metadata.kit_version` field as the way to see which version is installed.

## Evidence (run folders from the experiment; readiness output in `02-readiness.json`, field `accelerators_missed`)

- `runs/07-lab-results-aggregator/20261124-194018/`: says the DocumentDB skills are already installed and still lists the kit as missing
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/`
- `runs/02-transaction-categorization-agent/20261124-190028/`: says the kit is "not present as a single npx package"
- `runs/09-trade-settlement-tracker/20261124-201323/`
- `runs/09-inventory-reorder-multi-agent-system/20261125-054042/`: a repeat run with the same result

In every run, `skills-lock.json` pinned all 17 skills to `Azure/documentdb-agent-kit` at `4f41c15`; they were installed with `npx skills add`.

## Verification

### 1. Already covered? confirmed (not covered)

I searched the kit clone at commit `4f41c15` (2026-11-23):
- `AGENTS.md` line 43, Route B step 1, checks only for `~/.agents/skills/find-skills/`. No step checks whether the kit itself is installed. Searching `AGENTS.md`, all `skills/*/SKILL.md` and `docs/installation/verify.md` for "already installed", "is installed" and similar phrases found nothing relevant (the only hit is "Azure CLI installed?" in `azure-deployment`).
- `skills/mcp-setup/SKILL.md` has a "Fastest path: bundled installer" section at line 44 and no check for an existing install before it.
- `install.sh` line 595 and `install.ps1` line 537 only log "Kit installed at: ...". Neither writes a manifest, `kit.json` or a version file. There is no root `VERSION` file.
- None of the 17 `skills/*/SKILL.md` front matter blocks has a `metadata:` key (for example, `skills/mcp-setup/SKILL.md` has only `name` and `description`).
- `docs/installation/verify.md` has three steps, all about the MCP server, and none that checks the skills.
Nothing in the kit covers what the draft asks for.

### 2. Is the premise true? confirmed (with small factual corrections applied)

- Confirmed: `CHANGELOG.md` line 65 (2026-05-21 entry) says it "Replaced the non-functional `npx skills add Azure/documentdb-agent-kit` placeholder". `README.md` line 131, `README.md` line 136, `AGENTS.md` line 109, `docs/installation/skills-only.md` line 6 and `docs/installation/updating.md` lines 8 and 22 all present the command as the skills-only install and update path. Correction applied: the same 2026-05-21 entry, at line 125, also says the README documents the npx one-liner, so the contradiction is inside a single CHANGELOG entry and the body now says so.
- Confirmed: plugin manifests at `"version": "0.1.0"` (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`). There is no `VERSION` file. Correction applied: the draft hard-coded `0.2.0`. That number appears only in a CHANGELOG heading ("v0.2.0") and conflicts with the manifests, so the body now uses a placeholder stamped from `VERSION`.
- Confirmed: the installer flags exist as named: `--dry-run`, `--uninstall`, `--mcp-only` in `install.sh` lines 15-19, and `-DryRun`, `-Uninstall`, `-McpOnly` in `install.ps1` lines 56-60. `--uninstall` already removes `~/.documentdb-agent-kit` (`install.sh` line 16), so the body now says the marker goes with it instead of asking for new uninstall logic. `install_skills_for_client` and `main()` exist (`install.sh` lines 385, 539 and 589).
- Confirmed: the Agent Skills specification (agentskills.io) defines an optional `metadata` field as a map of string keys to string values. The body now quotes the values.
- Confirmed from the experiment: `/Users/julietai/claude/azure-documentdb-agent-readiness/skills-lock.json` lists 17 skills with `"source": "Azure/documentdb-agent-kit"`. `.agents/skills/` holds the 17 `documentdb-*` directories. `runs/07-lab-results-aggregator/20261124-194018/02-readiness.json` `accelerators_missed` lists the kit while saying the skills are already installed.
- The draft makes no Azure DocumentDB service claims that conflict with the known facts.

### 3. Maintainer skeptic: confirmed

The proposal names concrete files (`AGENTS.md`, `skills/mcp-setup/SKILL.md`, all `skills/*/SKILL.md` front matter, `install.sh`, `install.ps1`, the four plugin manifests, `CHANGELOG.md`, `README.md`, `docs/installation/{verify,skills-only,updating}.md`) and concrete edits. It fixes a documented self-contradiction in the kit's own install story and an agent-routing gap that is specific to this kit. It is not generic hygiene. Its scope belongs in this repository; the harness-side half is filed separately. As a maintainer I would accept it, with the version number settled at PR time. If reviewers prefer smaller PRs, item 4 (the docs fixes) can be split out.

## Finding ids

F0016, F0087, F0125, F0192, F0331, F0363, F0471, F0509, F0538, F0570, F0673, F0739, F0807, F0898, F0928, F0955, F1086, F1176, F1350, F1384, F1415, F1446, F1501, F1571
