"""Read-only preliminaries for m-cli. Run: python -I pre.py

Records: tool versions, whether this shell has a TTY, --help of update/create/delete/
check-name-availability, the resource group location, the resource list baseline and
name availability of the two short-lived cluster names.
"""
import json
import os
import sys

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-cli"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

RG, CL = common.RG, common.CLUSTER

common.record("p0-shell-tty", kind="derived", command="python: sys.stdin.isatty() / os.isatty(0) in the agent's Bash tool process",
              stdin_isatty=sys.stdin.isatty(), note="pre.py itself is launched from the agent's Bash tool")
common.az("p1-az-version", ["version", "-o", "json"])
common.az("p2-extension-list", ["extension", "list", "--query", "[].{name:name, version:version, preview:preview, experimental:experimental}", "-o", "json"])
common.az("p3-dynamic-install-config", ["config", "get", "extension", "-o", "json"])
for sub in ("update", "create", "delete", "check-name-availability", "wait"):
    common.az(f"p4-help-{sub}", ["documentdb", "mongocluster", sub, "--help"], parse_json=False, quiet=True)
common.az("p5-rg-show", ["group", "show", "-n", RG, "--query", "{name:name, location:location, provisioningState:properties.provisioningState}", "-o", "json"])
common.az("p6-resource-list-baseline", ["resource", "list", "-g", RG, "--query", "[].{name:name, type:type, location:location, tags:tags}", "-o", "json"])
common.az("p7-mongocluster-list-baseline", ["documentdb", "mongocluster", "list", "-g", RG,
                                            "--query", "[].{name:name, serverVersion:properties.serverVersion, tier:properties.compute.tier, provisioningState:properties.provisioningState, clusterStatus:properties.clusterStatus}",
                                            "-o", "json"])
for name in ("ddb-ver-test-50", "ddb-ver-test-60"):
    common.az(f"p8-name-availability-{name}", ["documentdb", "mongocluster", "check-name-availability",
                                                "--location", "eastus", "--name", name,
                                                "--type", "Microsoft.DocumentDB/mongoClusters", "-o", "json"])
