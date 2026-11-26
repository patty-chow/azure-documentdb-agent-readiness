---
id: X02
title: "az documentdb mongocluster update --server-version help: say that leaving it out keeps the current version and that a lower value requests a downgrade"
repo: Azure/azure-cli-extensions
type: issue
status: ready
priority: P2
sample_count: 0
member_drafts: []
open_questions: 2
---

# az documentdb mongocluster update --server-version help: say that leaving it out keeps the current version and that a lower value requests a downgrade

## What happens today

`az documentdb mongocluster update --help` (documentdb extension 1.0.0, azure-cli 2.89.1, recorded 2026-11-25) gives `--server-version` the same help as `create`: "The Mongo DB server version. Defaults to the latest available version if not specified." The sentence is the REST spec's `serverVersion` description (DECISIONS.md, SME topic 11), and it fits `create`, where the service picks the latest version when the property is omitted. On `update` it contradicts the command's own summary, "Only the properties specified in the request are modified; all other properties are left unchanged (HTTP PATCH)", and the 1.0.0 source: `update` reads the cluster (`MongoClustersGet`), applies the given arguments to that body and sends it back as the PATCH (`aaz/latest/documentdb/mongocluster/_update.py`, `_execute_operations`), so when the flag is left out the PATCH carries the current version and the cluster keeps it. That reading comes from the source, not from a test: the only update without the flag that was run (`--auth-allowed-modes` only, which returned `serverVersion` 8.0) was on a cluster already at the latest version, so it cannot tell the two readings apart.

The help also does not say what a lower value does, and the CLI does not check it. In a managed-service test on 2026-11-25, `az documentdb mongocluster update --server-version 7.0` on an 8.0 cluster (M30, one shard, Premium SSD v2, high availability off) exited 0 after 94 seconds with empty stderr and no warning; `hello` then reported wire version 21 instead of 25 and `buildInfo` 7.0.0, with the same engine build. The returned body still read `Updating`; `show` reported `Succeeded` and `Ready` afterwards. Raising the version back to 8.0 took 128 seconds, and 145 of 145 once-a-second probes (`hello`, an insert and a count) succeeded during that change. That is one downgrade, accepted in one test on one cluster shape. A Microsoft Q&A thread (question 5860936) describes a downgrade on a Free-tier cluster that ended in `UpdateFailed` with 409 Conflict, and no Learn, CLI or ARM reference page says whether a downgrade is supported. (Checked 2026-11-25.)

## Why it matters

Agents and scripts read `--help`, and the generated reference page (https://learn.microsoft.com/cli/azure/documentdb/mongocluster) built from it, to decide what a flag does. Read on `update`, "Defaults to the latest available version if not specified" suggests that an update without the flag can move the cluster to the latest version, and nothing says that a lower value is sent as is and requests a downgrade, which the service accepted without warning in the one test and which ended in a failed cluster in the Q&A report. The Agent Kit item K20 asks the kit to tell agents not to lower `--server-version`; the CLI help is the other place an agent looks.

No run of the experiment executed `az documentdb mongocluster update` (Azure writes were off; the runs used only `show`, `list` and `list-connection-strings`, per DECISIONS.md topic 5), so there is no sample count; the evidence is the managed-service test.

## Proposed change

The reference page is generated from the extension's help text, so the fix belongs in this repository's `src/documentdb`.

1. **`documentdb` extension, `az documentdb mongocluster update --server-version` help.** Override the argument's help on `update` only, the way the extension's `custom.py` already overrides the `--admin-password` help for `reset-password` (`ResetPassword._build_arguments_schema` sets `_help["short-summary"]`, documentdb 1.0.0), with:
   > The MongoDB server version to change the cluster to. If not specified, the current version is kept. A value lower than the current version is not checked by the CLI and requests a downgrade.

   Leave the `create` help as it is: there the sentence describes the service default.

2. **Optional: warn before a downgrade.** `update` already reads the cluster before it sends the PATCH, and the generated command passes that body to `pre_instance_update`, so an override can compare the requested version with the current `serverVersion` and print a warning when it is lower. Whether a lower value should be rejected instead is for the service owners (open question 1).

Constraints for the wording: one downgrade on one cluster shape was observed, and a Q&A report describes one that failed, so the help must not call a downgrade supported or unsupported until the owners say which; it states what the command does.

## Evidence

Files in the experiment repository, under `findings/phase4/engine-tests-managed/`:

- `m-cli/report.json`, step `p4-help-update`: the `update` help with its summary line and the `--server-version` sentence (documentdb 1.0.0, azure-cli 2.89.1); step `p4-help-create`: the same sentence on `create`.
- `m-cli/report.json`, steps `a0-hello-before`, `a1-state-before`, `a2-update-server-version-7.0`, `a4-state-after`, `a5-hello-after` and `a6-buildinfo-after`: wire version 25 and `serverVersion` 8.0 before; the update (exit 0 after 93.5 seconds, empty stderr, returned body still `Updating`); `serverVersion` 7.0, `Succeeded` and `Ready` after; wire version 21 and `buildInfo` 7.0.0. `m-cli/review.json` limits the conclusion to "did not stop this downgrade".
- `m-cli-upgrade/upgrade.start`, `upgrade.end` and `pings.jsonl`: the update back to 8.0 (128 seconds between the two timestamps; 145 of 145 probes succeeded; the first wire-25 reply at about +88 seconds). This probe had no per-test reviewer; its numbers were re-checked separately.
- `m-entra/report.json`, step `b1`: an update with only `--auth-allowed-modes` returned `serverVersion` 8.0.

## Resolved

- Does the control plane block a downgrade? Not in the one case tested (8.0 to 7.0; M30, one shard, high availability off): no error and no warning, and the cluster went back to 8.0 without a failed probe. The Q&A answer that calls downgrades unsupported cites no documentation, and the Q&A cluster (Free tier) ended in `UpdateFailed` with 409, so the issue claims neither "always accepted" nor "always rejected". Sources: the m-cli and m-cli-upgrade files above; ENGINE-TESTS.md, Managed service; DECISIONS.md, SME topic 11, open item 2.

## Open questions

1. Maintainer decision: add the warning in proposed change 2, or only fix the help text? Whether the service supports a downgrade at all is not documented (DECISIONS.md, SME topic 11); the proposed help text does not depend on the answer.
2. "Leaving the flag out keeps the current version" is read from the 1.0.0 source and the command's summary, not observed: the only update without the flag ran on a cluster already at the latest version. Observing it needs an update without the flag on a cluster below the latest version. Internal check, not an SME question.

## Source drafts

None: this item comes from the managed-service test of 2026-11-25, not from a phase-4 draft.

## Finding ids

None: no run executed `az documentdb mongocluster update`.
