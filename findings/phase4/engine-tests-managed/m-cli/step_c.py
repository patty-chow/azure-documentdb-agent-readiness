"""Step (c): which --server-version values a NEW cluster accepts.

Run: python -I step_c.py <phase> [args]
  create <name> <version> <tier> <storage-gb>   one create with --no-wait, then an immediate show
  poll <seconds> <name> [<name> ...]            show every 30 s until each is in a terminal state or time is up
  delete <name> [<name> ...]                    delete --yes --no-wait, then an immediate show
  gone <seconds> <name> [<name> ...]            show until ResourceNotFound, then az resource list -g RG
  activity <minutes>                            activity-log entries for the two test clusters (only when needed)

The admin password is generated here with secrets, registered with the masker, passed to az in
argv only, and never printed or written anywhere.
"""
import json
import secrets
import string
import sys
import time

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-cli"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

RG = common.RG
ALLOWED = {"ddb-ver-test-50", "ddb-ver-test-60"}  # this script never acts on any other cluster
ADMIN_USER = "vertestadmin"
SHOW_QUERY = ("{name:name, location:location, serverVersion:properties.serverVersion, "
              "provisioningState:properties.provisioningState, clusterStatus:properties.clusterStatus, "
              "tier:properties.compute.tier, storage:properties.storage, shardCount:properties.sharding.shardCount, "
              "haTargetMode:properties.highAvailability.targetMode, publicNetworkAccess:properties.publicNetworkAccess, "
              "authAllowedModes:properties.authConfig.allowedModes, previewFeatures:properties.previewFeatures, "
              "tags:tags, createdAt:systemData.createdAt, lastModifiedAt:systemData.lastModifiedAt}")
TERMINAL = {"Succeeded", "Failed", "Canceled"}


def check(name):
    if name not in ALLOWED:
        raise SystemExit(f"refusing to act on {name!r}")


def gen_password(n=24):
    alphabet = string.ascii_letters + string.digits
    while True:
        chars = [secrets.choice(alphabet) for _ in range(n - 1)]
        if any(c.islower() for c in chars) and any(c.isupper() for c in chars) and any(c.isdigit() for c in chars):
            break
    chars.insert(secrets.randbelow(n - 2) + 1, "!")  # fourth character class, never first or last
    return "".join(chars)


def show(step_id, name, quiet=False):
    return common.az(step_id, ["documentdb", "mongocluster", "show", "--resource-group", RG, "--name", name,
                               "--query", SHOW_QUERY, "-o", "json"], quiet=quiet)


phase = sys.argv[1]

if phase == "create":
    name, version, tier, size = sys.argv[2:6]
    check(name)
    pw = gen_password()
    common.add_secret(pw, "<generated-password-masked>")
    args = ["documentdb", "mongocluster", "create", "--resource-group", RG, "--name", name,
            "--server-version", version, "--tier", tier, "--storage-size", size, "--shard-count", "1",
            "--high-availability", "Disabled", "--admin-user", ADMIN_USER, "--admin-password", pw,
            "--tags", "purpose=samples-factory", "--no-wait"]
    display = common.mask(" ".join(["az"] + args))
    assert "<generated-password-masked>" in display and pw not in display
    tag = f"{name}-{tier}"
    common.az(f"c1-create-{tag}", args, display=display,
              extra={"password_note": "24-character random password (letters, digits and one '!') generated with "
                                      "Python secrets in step_c.py; passed in argv only, never printed or written"})
    del pw
    show(f"c2-show-after-create-{tag}", name)

elif phase == "poll":
    seconds = int(sys.argv[2])
    names = sys.argv[3:]
    for n in names:
        check(n)
    deadline = time.time() + seconds
    pending = set(names)
    i = 0
    while pending and time.time() < deadline:
        i += 1
        for n in sorted(pending):
            rec, out, err, code = show(f"c3-poll-{n}-{int(time.time())}", n, quiet=True)
            st = rec.get("stdout_json") or {}
            print(json.dumps({"t": common.now_iso(), "name": n, "exit": code,
                              "serverVersion": st.get("serverVersion"),
                              "provisioningState": st.get("provisioningState"),
                              "clusterStatus": st.get("clusterStatus"),
                              "stderr": (rec.get("stderr") or "")[:400]}))
            if code == 0 and st.get("provisioningState") in TERMINAL:
                pending.discard(n)
            if code not in (0, None) and "ResourceNotFound" in (rec.get("stderr") or ""):
                pending.discard(n)
        if pending:
            time.sleep(30)
    print(json.dumps({"still_pending": sorted(pending)}))

elif phase == "delete":
    for n in sys.argv[2:]:
        check(n)
        common.az(f"c4-delete-{n}", ["documentdb", "mongocluster", "delete", "--resource-group", RG, "--name", n,
                                     "--yes", "--no-wait"])
        show(f"c5-show-after-delete-{n}", n)

elif phase == "gone":
    seconds = int(sys.argv[2])
    names = sys.argv[3:]
    for n in names:
        check(n)
    deadline = time.time() + seconds
    pending = set(names)
    while pending and time.time() < deadline:
        for n in sorted(pending):
            rec, out, err, code = show(f"c6-gone-poll-{n}-{int(time.time())}", n, quiet=True)
            st = rec.get("stdout_json") or {}
            print(json.dumps({"t": common.now_iso(), "name": n, "exit": code,
                              "provisioningState": st.get("provisioningState"),
                              "clusterStatus": st.get("clusterStatus"),
                              "stderr": (rec.get("stderr") or "")[:400]}))
            if code not in (0, None) and ("ResourceNotFound" in (rec.get("stderr") or "")
                                          or "not found" in (rec.get("stderr") or "").lower()):
                pending.discard(n)
        if pending:
            time.sleep(30)
    print(json.dumps({"still_present": sorted(pending)}))
    common.az("c7-resource-list-after", ["resource", "list", "-g", RG,
                                         "--query", "[].{name:name, type:type, location:location, tags:tags}", "-o", "json"])

elif phase == "activity":
    minutes = int(sys.argv[2])
    common.az("c8-activity-log", ["monitor", "activity-log", "list", "--resource-group", RG, "--offset", f"{minutes}m",
                                  "--query", "[?contains(resourceId, 'ddb-ver-test')].{time:eventTimestamp, op:operationName.value, "
                                             "status:status.value, subStatus:subStatus.value, resource:resourceId, "
                                             "statusMessage:properties.statusMessage}", "-o", "json"])
else:
    raise SystemExit(f"unknown phase {phase}")
