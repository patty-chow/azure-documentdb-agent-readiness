"""az CLI steps for m-entra. Run: python -I az_steps.py <phase>

phases: a (before), b_help, b (enable Entra + poll), c (help), d_id, d_assign, d_verify, after
Every call is recorded (masked) in raw/steps.jsonl by common.run().
"""
import json
import sys
import time

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

RG = common.ENV["MANAGED_RG"]
CL = common.ENV["MANAGED_CLUSTER"]
OID = common.IDS.get("oid")
phase = sys.argv[1]


def az(step_id, args, parse_json=True, timeout=590, extra=None):
    rec, out, err, code = common.run(step_id, ["az"] + args, parse_json=parse_json, timeout=timeout, extra=extra)
    summary = {"id": step_id, "exit": code, "dur_s": rec["duration_s"]}
    if rec.get("stdout_json") is not None:
        summary["json"] = rec["stdout_json"]
    else:
        summary["stdout_head"] = (rec.get("stdout") or "")[:600]
    if rec.get("stderr"):
        summary["stderr_head"] = rec["stderr"][:1200]
    print(json.dumps(summary, indent=1)[:4000])
    return rec, out, err, code


def show_state(step_id):
    return az(step_id, ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", CL,
                        "--query", "{authConfig: properties.authConfig, provisioningState: properties.provisioningState, "
                                   "clusterStatus: properties.clusterStatus, lastModifiedAt: systemData.lastModifiedAt}",
                        "-o", "json"])


if phase == "a":
    az("a1-authConfig-before", ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", CL,
                                "--query", "properties.authConfig", "-o", "json"])
    az("a2-show-before", ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", CL, "-o", "json"])
    az("a3-connection-strings-before", ["documentdb", "mongocluster", "list-connection-strings",
                                        "--resource-group", RG, "--cluster-name", CL, "-o", "json"])

elif phase == "b_help":
    rec, out, err, code = common.run("b0-update-help", ["az", "documentdb", "mongocluster", "update", "--help"])
    # print only the auth-related part
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if "auth" in ln.lower():
            print("\n".join(lines[max(0, i - 1):i + 6]))
            print("...")

elif phase == "b":
    t0 = time.time()
    rec, out, err, code = az("b1-update-auth-allowed-modes",
                             ["documentdb", "mongocluster", "update", "--name", CL, "--resource-group", RG,
                              "--auth-allowed-modes", "NativeAuth", "MicrosoftEntraID"])
    t_cmd = time.time() - t0
    polls = []
    deadline = time.time() + 540
    i = 0
    while time.time() < deadline:
        i += 1
        r, o, e, c = show_state(f"b2-poll-{i}")
        st = r.get("stdout_json") or {}
        polls.append({"t_since_update_start_s": round(time.time() - t0, 1), "state": st})
        if st.get("provisioningState") == "Succeeded" and st.get("clusterStatus") == "Ready" and \
                "MicrosoftEntraID" in ((st.get("authConfig") or {}).get("allowedModes") or []):
            break
        time.sleep(15)
    common.record("b3-time-to-apply", kind="derived",
                  command="wall time of the update command (CLI waits for the long-running operation) and of the follow-up show polls",
                  update_command_wall_s=round(t_cmd, 1), polls=polls)
    print(json.dumps({"update_wall_s": round(t_cmd, 1), "polls": len(polls), "last": polls[-1] if polls else None}, indent=1))

elif phase == "c":
    common.run("c1-mongocluster-help", ["az", "documentdb", "mongocluster", "--help"])
    common.run("c2-entra-user-help", ["az", "documentdb", "mongocluster", "microsoft-entra-user", "--help"])
    rec, out, err, code = common.run("c3-entra-user-assign-help",
                                     ["az", "documentdb", "mongocluster", "microsoft-entra-user", "assign", "--help"])
    print(out)
    for sub in ("list", "show", "remove"):
        common.run(f"c4-entra-user-{sub}-help", ["az", "documentdb", "mongocluster", "microsoft-entra-user", sub, "--help"])
    r2, o2, e2, c2 = common.run("c5-entra-user-group-help-print", ["az", "documentdb", "mongocluster", "microsoft-entra-user", "--help"])
    print(o2)

elif phase == "d_id":
    rec, out, err, code = common.run("d1-signed-in-user-id", ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"])
    print(json.dumps({"stdout": rec["stdout"], "exit": code, "stderr": rec["stderr"][:500]}))
    # Characterise the account type without recording personal fields.
    az("d1b-signed-in-user-type",
       ["rest", "--method", "GET", "--url",
        "https://graph.microsoft.com/v1.0/me?$select=userType,creationType,externalUserState,identities,userPrincipalName",
        "--query", "{userType: userType, creationType: creationType, externalUserState: externalUserState, "
                   "upnHasExtMarker: contains(userPrincipalName, '#EXT#'), "
                   "identities: identities[].{signInType: signInType, issuer: issuer}}",
        "-o", "json"])

elif phase == "d_assign":
    if not OID:
        raise SystemExit("no object id")
    t0 = time.time()
    az("d2-entra-user-assign",
       ["documentdb", "mongocluster", "microsoft-entra-user", "assign",
        "--object-id", OID, "--cluster-name", CL, "--resource-group", RG,
        "--type", "User", "--role", "db=admin", "role=root"])
    common.record("d2b-assign-wall", kind="derived", command="wall time of the assign command", wall_s=round(time.time() - t0, 1))

elif phase == "d_verify":
    az("d3-entra-user-list", ["documentdb", "mongocluster", "microsoft-entra-user", "list",
                              "--cluster-name", CL, "--resource-group", RG, "-o", "json"])
    az("d4-entra-user-show", ["documentdb", "mongocluster", "microsoft-entra-user", "show",
                              "--object-id", OID, "--cluster-name", CL, "--resource-group", RG, "-o", "json"])
    sub = common.IDS["subscription"]
    az("d5-arm-users-list", ["rest", "--method", "GET", "--url",
                             f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{RG}/providers/"
                             f"Microsoft.DocumentDB/mongoClusters/{CL}/users?api-version=2026-06-01", "-o", "json"])

elif phase == "after":
    az("z1-authConfig-after", ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", CL,
                               "--query", "properties.authConfig", "-o", "json"])
    az("z2-show-after", ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", CL, "-o", "json"])
    az("z3-connection-strings-after", ["documentdb", "mongocluster", "list-connection-strings",
                                       "--resource-group", RG, "--cluster-name", CL, "-o", "json"])
else:
    raise SystemExit("unknown phase")
