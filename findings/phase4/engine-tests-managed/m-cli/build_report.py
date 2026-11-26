"""Assemble report.json for m-cli from raw/steps.jsonl (already masked) plus the readings below.
Run: python -I build_report.py
"""
import json
import os
import sys

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-cli"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

recs = [json.loads(l) for l in open(os.path.join(TEST_DIR, "raw", "steps.jsonl"))]
by_id = {r["id"]: r for r in recs}

STEP = {
    "p0-shell-tty": ("Does the agent's own shell give az a TTY?",
                     "The agent's Bash tool runs commands with a non-TTY stdin, so any az call it makes takes the no-prompt dynamic-install path by default.",
                     "n/a"),
    "p1-az-version": ("Client versions", "azure-cli 2.89.1 with the documentdb extension 1.0.0 (plus account 0.2.5 and cosmosdb-preview 1.7.0) in the user's normal config dir.", "n/a"),
    "p2-extension-list": ("Installed extensions in the normal config dir", "documentdb 1.0.0 is installed in the normal config dir and is not a preview build, so steps a and c use the stable command surface.", "n/a"),
    "p3-dynamic-install-config": ("Dynamic-install configuration", "No extension.* keys are configured (empty list), so use_dynamic_install, dynamic_install_allow_preview and run_after_dynamic_install all take their built-in defaults.", "n/a"),
    "p4-help-update": ("update --help (flag names for step a)", "The downgrade flag is --server-version; its help says only 'Defaults to the latest available version if not specified' and nothing restricts it to upgrades or warns that a lower value downgrades; the command is described as an HTTP PATCH (the 1.0.0 source does GET, edits the body, then PATCH at api-version 2026-06-01).", "n/a"),
    "p4-help-create": ("create --help (flags for step c)", "Required: --admin-password, --admin-user, --name, --resource-group, --high-availability, --shard-count, --storage-size, --tier; --server-version is a free string; the summary line still says 'Update overwrites all properties for the resource'.", "n/a"),
    "p4-help-delete": ("delete --help (flags for step c)", "delete takes --yes to skip the confirmation prompt and --no-wait; it was never run because no cluster was created.", "n/a"),
    "p4-help-check-name-availability": ("check-name-availability --help", "Takes --location, --name and --type (default Microsoft.DocumentDB/mongoClusters).", "n/a"),
    "p4-help-wait": ("wait --help", "wait supports --created, --deleted, --exists and --custom with a 30 s default interval and 3600 s timeout; recorded for completeness.", "n/a"),
    "p5-rg-show": ("Resource group location", "documentdb-samples-rg is in eastus, which the create commands of step c would have inherited.", "n/a"),
    "p6-resource-list-baseline": ("Resource baseline before the test", "The resource group held exactly one resource, the shared cluster ddb-samples-shared.", "n/a"),
    "p7-mongocluster-list-baseline": ("Cluster baseline before the test", "ddb-samples-shared was serverVersion 8.0, M30, Succeeded and Ready before the test.", "n/a"),
    "p8-name-availability-ddb-ver-test-50": ("Name ddb-ver-test-50 available?", "The name was available globally (nameAvailable true), so a create would not have failed on the name.", "n/a"),
    "p8-name-availability-ddb-ver-test-60": ("Name ddb-ver-test-60 available?", "The name was available globally (nameAvailable true).", "n/a"),
    "a0-hello-before": ("(a) hello before the downgrade", "Before the attempt the gateway advertised maxWireVersion 25 (MongoDB 8.0) with engine versions 2.2-1, 2.3.0 and 12.1-1; documentdb-local 0.117 and 1.2.0 advertise wire version 21 (7.0.0), so this differs from the open-source image.", "different"),
    "a1-state-before": ("(a) control-plane state before the downgrade", "serverVersion 8.0, provisioningState Succeeded, clusterStatus Ready, M30, PremiumSSDv2 128 GB, HA Disabled, auth modes MicrosoftEntraID and NativeAuth (left by m-entra).", "n/a"),
    "a2-update-server-version-7.0": ("(a) az documentdb mongocluster update --server-version 7.0 on the 8.0 cluster",
                                     "The control plane accepted the downgrade: no error, exit code 0 after 93.5 s, and the returned resource already showed serverVersion 7.0 while provisioningState and clusterStatus still read Updating.",
                                     "n/a"),
    "a2b-update-wall": ("(a) wall time of the update", "The CLI waited 93.5 s for the long-running operation.", "n/a"),
    "a5-hello-after": ("(a) hello after the downgrade", "After the downgrade the gateway advertises maxWireVersion 21 (MongoDB 7.0) with unchanged engine versions 2.2-1, 2.3.0, 12.1-1, so the version switch is a wire-compatibility level on the same engine build; wire 21 is what documentdb-local 0.117 and 1.2.0 advertise.", "same"),
    "a6-buildinfo-after": ("(a) buildInfo after the downgrade", "buildInfo now reports version 7.0.0 / versionArray [7,0,0,0] where sibling tests recorded 8.0.0 earlier the same day; documentdb-local also advertises 7.0.0.", "same"),
    "a4-state-after": ("(a) control-plane state after the downgrade", "The cluster settled at serverVersion 7.0, provisioningState Succeeded, clusterStatus Ready, with every other property unchanged.", "n/a"),
    "a7-activity-log": ("(a) activity log three minutes after the update", "ARM logged the write as Started then Accepted (HTTP 202) at 23:16:14Z, then 'read' events with status Running at about 15 s intervals, which fits the CLI polling the long-running operation; the final event had not been ingested yet.", "n/a"),
    "a7b-activity-log-recheck": ("(a) activity log re-checked", "The same write finished as Succeeded at 23:17:47.8Z with no statusMessage, about 94 s after it was accepted, so the platform records the downgrade as a normal successful update.", "n/a"),
    "b1-mktemp": ("(b) brand-new config dir", "mktemp -d created a fresh directory under the scratchpad root to serve as AZURE_CONFIG_DIR.", "n/a"),
    "b1-mktemp-contents": ("(b) config dir is empty", "The new directory was empty before az ran.", "n/a"),
    "b1b-env": ("(b) child environment", "Only AZURE_CONFIG_DIR was set for the child; AZURE_EXTENSION_DIR was not set in the parent and was removed from the child, and stdin was /dev/null.", "n/a"),
    "b2-first-run-no-tty": ("(b) az documentdb mongocluster list in the fresh dir with stdin from /dev/null",
                            "No prompt: az printed four WARNING lines (preview installs disabled by default; how to configure that; 'The command requires the extension documentdb. It will be installed first.'; a later preview version exists), installed the extension, re-ran the command, and exited 1 only because the fresh dir has no login ('ERROR: Please run 'az login' to setup account.'); nothing went to stdout and the whole run took 3.8 s.",
                            "n/a"),
    "b3-config-dir-after-first-run": ("(b) what the first run wrote", "The run downloaded extensionCommandTree.json (241,107 bytes) and installed cliextensions/documentdb from documentdb-1.0.0-py3-none-any.whl (97,139 bytes), the stable build rather than the 1.1.0b2 preview.", "n/a"),
    "b4-extension-list-in-temp-dir": ("(b) extension list in the temp dir", "The auto-installed extension is documentdb 1.0.0, preview false, installed under the temporary config dir.", "n/a"),
    "b5-second-run-no-tty": ("(b) second identical run", "With the extension present the second run printed only 'ERROR: Please run 'az login' to setup account.' and exited 1 in 0.19 s, so the install happens once per config dir.", "n/a"),
    "b6-remove-temp-dir": ("(b) remove the temp dir", "shutil.rmtree succeeded and the path was gone immediately afterwards.", "n/a"),
    "b6b-temp-dir-recreated-then-removed": ("(b) temp dir reappeared and was removed again", "The Azure CLI telemetry uploader, which az starts in the background after a command, wrote logs/telemetry.log a moment after b6 and so recreated the dir; it was removed again and stayed gone, so scripts that delete a throwaway AZURE_CONFIG_DIR right after az exits should wait or disable telemetry.", "n/a"),
    "b7-mktemp-tty": ("(b, contrast) second fresh config dir for a TTY run", "A second empty directory was created for the pseudo-terminal contrast.", "n/a"),
    "b7-mktemp-tty-contents": ("(b, contrast) dir is empty", "The second directory was empty before az ran.", "n/a"),
    "b8-first-run-pty": ("(b, contrast) the same command on a pseudo-terminal, answering n",
                         "With a TTY az blocks on 'The command requires the extension documentdb. Do you want to install it now? The command will continue to run after the extension is installed. (Y/n):' (default Y); answering n printed 'The command requires the latest version of extension documentdb. To install, run 'az extension add --upgrade -n documentdb'.' and exited 2 without installing anything.",
                         "n/a"),
    "b8b-correction": ("(b, contrast) correction of b8's timed_out flag", "b8's timed_out=true is a script bookkeeping error (the loop ended on pty EOF after 1.54 s); the run did not time out and az exited normally with code 2.", "n/a"),
    "b9-config-dir-after-pty-run": ("(b, contrast) what the TTY run wrote", "After the declined prompt the dir held the downloaded extensionCommandTree.json but no cliextensions folder, confirming nothing was installed.", "n/a"),
    "b10-remove-temp-dir-tty": ("(b, contrast) remove the second temp dir", "Removed after waiting for the telemetry uploader; it did not reappear.", "n/a"),
    "c1-create-ddb-ver-test-50-M10": ("(c) create ddb-ver-test-50 with --server-version 5.0, M10, 32 GB, --no-wait",
                                      "Refused by local permissions before it ran (Claude Code auto-mode classifier, 'Destructive or Unwanted Actions'), so no password was generated and no request reached Azure; the 5.0 question stays open.",
                                      "n/a"),
    "c1-create-ddb-ver-test-60-M10": ("(c) create ddb-ver-test-60 with --server-version 6.0, M10, 32 GB, --no-wait",
                                      "Not attempted: the spec says to record a local refusal and skip, and the same action class had just been refused; the 6.0 question stays open.",
                                      "n/a"),
    "c9-verify-absent-show-ddb-ver-test-50": ("(c) confirm no cluster ddb-ver-test-50 exists", "show returned ResourceNotFound (exit 3), confirming the refused create left nothing behind.", "n/a"),
    "c9-verify-absent-show-ddb-ver-test-60": ("(c) confirm no cluster ddb-ver-test-60 exists", "show returned ResourceNotFound (exit 3).", "n/a"),
    "c9-verify-absent-resource-list": ("(c) az resource list -g documentdb-samples-rg after the skip", "The resource group still holds only ddb-samples-shared, so there was nothing to delete.", "n/a"),
}

ORDER = [
    "p0-shell-tty", "p1-az-version", "p2-extension-list", "p3-dynamic-install-config",
    "p4-help-update", "p4-help-create", "p4-help-delete", "p4-help-check-name-availability", "p4-help-wait",
    "p5-rg-show", "p6-resource-list-baseline", "p7-mongocluster-list-baseline",
    "p8-name-availability-ddb-ver-test-50", "p8-name-availability-ddb-ver-test-60",
    "a0-hello-before", "a1-state-before", "a2-update-server-version-7.0", "a2b-update-wall",
    "a4-poll-*", "a5-hello-after", "a6-buildinfo-after", "a4-state-after", "a7-activity-log", "a7b-activity-log-recheck",
    "b1-mktemp", "b1-mktemp-contents", "b1b-env", "b2-first-run-no-tty", "b3-config-dir-after-first-run",
    "b4-extension-list-in-temp-dir", "b5-second-run-no-tty", "b6-remove-temp-dir", "b6b-temp-dir-recreated-then-removed",
    "b7-mktemp-tty", "b7-mktemp-tty-contents", "b8-first-run-pty", "b8b-correction", "b9-config-dir-after-pty-run",
    "b10-remove-temp-dir-tty",
    "c1-create-ddb-ver-test-50-M10", "c1-create-ddb-ver-test-60-M10",
    "c9-verify-absent-show-ddb-ver-test-50", "c9-verify-absent-show-ddb-ver-test-60", "c9-verify-absent-resource-list",
]


def response_of(r):
    skip = {"id", "recorded_at", "command"}
    return {k: v for k, v in r.items() if k not in skip}


steps = []
seen = set()
for key in ORDER:
    if key.endswith("*"):
        matches = [r for r in recs if r["id"].startswith(key[:-1])]
        for r in matches:
            st = r.get("stdout_json") or {}
            steps.append({"id": r["id"], "step": "(a) poll show after the update returned",
                          "command": r["command"], "response": response_of(r),
                          "reading": f"{r.get('started_at')}: serverVersion {st.get('serverVersion')}, provisioningState {st.get('provisioningState')}, clusterStatus {st.get('clusterStatus')}; the first poll, 23 s after the CLI returned, already showed the downgrade complete.",
                          "vs_open_source": "n/a"})
            seen.add(r["id"])
        continue
    r = by_id[key]
    title, reading, vs = STEP[key]
    steps.append({"id": key, "step": title, "command": r.get("command"), "response": response_of(r),
                  "reading": reading, "vs_open_source": vs})
    seen.add(key)
missing = [r["id"] for r in recs if r["id"] not in seen]
assert not missing, missing

conclusions = json.load(open(os.path.join(TEST_DIR, "conclusions.json")))

report = {
    "test": "m-cli",
    "goal": "CLI and control-plane behaviour: (a) server-version downgrade on the 8.0 test cluster; (b) first-use dynamic install of the documentdb extension in a brand-new AZURE_CONFIG_DIR without a TTY; (c) which server versions a NEW cluster accepts (5.0, 6.0).",
    "database": "none (no database was read or written; the only data-plane calls were hello and buildInfo on admin)",
    "observed_on": "2026-11-25",
    "run_window_utc": {"started": recs[0]["recorded_at"], "finished": recs[-1]["recorded_at"]},
    "cluster": {
        "resource": "Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus",
        "shape_before": "M30, shardCount 1, serverVersion 8.0, PremiumSSDv2 128 GB, HA Disabled, public network access, auth modes MicrosoftEntraID + NativeAuth",
        "shape_after": "identical except serverVersion 7.0",
        "engine_identity_before": {"hello.maxWireVersion": 25, "hello.internal.documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"], "hello.internal.kind": "azuredocumentdb", "buildInfo.version": "8.0.0 (recorded by m-hosts, m-query and m-txn-bulk earlier on 2026-11-25)"},
        "engine_identity_after": {"hello.maxWireVersion": 21, "hello.internal.documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"], "hello.internal.kind": "azuredocumentdb", "buildInfo.version": "7.0.0"},
    },
    "client": {"az": "azure-cli 2.89.1 (Homebrew, Python 3.14), extension documentdb 1.0.0 (api-version 2026-06-01)",
               "python": "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python, PyMongo 4.20.1",
               "shell": "agent Bash tool, stdin not a TTY"},
    "sources_read_first": [
        "findings/phase4/DECISIONS.md, 'CLI, IaC and server versions (SME topic 11)': settled items on dynamic install without a TTY, accepted --server-version values at create time, in-place upgrade, required create parameters; open items 2 (downgrade) and 3 (5.0 and 6.0 for new clusters)",
        "findings/phase4/ENGINE-TESTS.md: no CLI or control-plane section (the open-source engine has no control plane); documentdb-local 0.117 and 1.2.0 advertise wire version 21 / MongoDB 7.0.0",
    ],
    "steps": steps,
    "config_changes": [
        "ddb-samples-shared properties.serverVersion changed from 8.0 to 7.0 with `az documentdb mongocluster update -g documentdb-samples-rg -n ddb-samples-shared --server-version 7.0` (started 2026-11-25T23:16:13Z; ARM write Accepted 23:16:14Z, Succeeded 23:17:47Z; CLI exit 0 after 93.5 s). Not reverted: the spec did not ask for it. The cluster now advertises hello.maxWireVersion 21 and buildInfo 7.0.0 instead of 25 / 8.0.0; any later test that assumes the 8.0 / wire-25 baseline needs `az documentdb mongocluster update -g documentdb-samples-rg -n ddb-samples-shared --server-version 8.0` first (not run here).",
    ],
    "not_config_changes": "No cluster was created or deleted: both creates in step (c) were refused locally or skipped, and show/resource list confirm the resource group still holds only ddb-samples-shared. No database was touched. Both temporary AZURE_CONFIG_DIRs (and the documentdb 1.0.0 copy auto-installed into the first) were removed and confirmed gone; AZURE_EXTENSION_DIR was never set; the user's normal ~/.azure configuration was not changed.",
    "scripts": {
        "common": os.path.join(TEST_DIR, "common.py"),
        "preliminaries": os.path.join(TEST_DIR, "pre.py"),
        "step_a": os.path.join(TEST_DIR, "step_a.py"),
        "step_b": os.path.join(TEST_DIR, "step_b.py"),
        "step_c": os.path.join(TEST_DIR, "step_c.py"),
        "build_report": os.path.join(TEST_DIR, "build_report.py"),
        "conclusions": os.path.join(TEST_DIR, "conclusions.json"),
        "raw_records": os.path.join(TEST_DIR, "raw", "steps.jsonl"),
    },
    "masking": "Password, URIs that carry it, subscription id, subscription name, tenant id/domain/name, object ids, e-mail addresses (systemData.createdBy, caller) and every other GUID (including correlation ids) are masked. step_c.py would have generated the new clusters' admin password in memory and registered it with the masker; because the create was refused before it ran, no such password was ever generated.",
    "conclusions": conclusions,
}
report = common.mask(report)
with open(os.path.join(TEST_DIR, "report.json"), "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("steps", len(steps), "conclusions", len(conclusions), "bytes", os.path.getsize(os.path.join(TEST_DIR, "report.json")))
