"""Step (a): attempt a server-version downgrade (8.0 -> 7.0) on the shared test cluster.

Run: python -I step_a.py <phase>
  before   state before the attempt
  update   az documentdb mongocluster update --server-version 7.0 (exactly as a user would run it)
  debug    the same command with --debug, to capture the HTTP method, status and error body (only after a
           synchronous rejection; the request carries no secret)
  after    state after the attempt
  hello    data-plane check: hello.maxWireVersion and internal.documentdb_versions (no database is touched)
"""
import json
import re
import sys
import time
import warnings

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-cli"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

RG, CL = common.RG, common.CLUSTER
STATE_QUERY = ("{serverVersion:properties.serverVersion, provisioningState:properties.provisioningState, "
               "clusterStatus:properties.clusterStatus, tier:properties.compute.tier, storage:properties.storage, "
               "shardCount:properties.sharding.shardCount, haTargetMode:properties.highAvailability.targetMode, "
               "authAllowedModes:properties.authConfig.allowedModes, publicNetworkAccess:properties.publicNetworkAccess, "
               "lastModifiedAt:systemData.lastModifiedAt}")
UPDATE_ARGS = ["documentdb", "mongocluster", "update", "-g", RG, "-n", CL, "--server-version", "7.0"]

phase = sys.argv[1]

if phase == "before":
    common.az("a1-state-before", ["documentdb", "mongocluster", "show", "-g", RG, "-n", CL, "--query", STATE_QUERY, "-o", "json"])

elif phase == "update":
    t0 = time.time()
    common.az("a2-update-server-version-7.0", UPDATE_ARGS, timeout=580)
    common.record("a2b-update-wall", kind="derived", command="wall time of the update command", wall_s=round(time.time() - t0, 1))

elif phase == "debug":
    rec, out, err, code = common.az("a3-update-server-version-7.0-debug", UPDATE_ARGS + ["--debug"], timeout=580, quiet=True)
    # Pull out the HTTP exchanges (method, URL, status, body) from the masked debug log.
    log = rec.get("stderr") or ""
    lines = log.splitlines()
    keep = []
    for i, ln in enumerate(lines):
        if re.search(r"Request URL:|Request method:|Response status:|Response content:|'x-ms-request-id'|'x-ms-correlation-request-id'|"
                     r"'x-ms-failure-cause'|'Azure-AsyncOperation'|'Location'|ERROR:|Command ran in|exit code", ln):
            keep.append(ln)
            if "Response content:" in ln and i + 1 < len(lines):
                keep.append(lines[i + 1][:4000])
        if "Request body:" in ln and i + 1 < len(lines):
            keep.append(ln)
            keep.append(lines[i + 1][:4000])
    common.record("a3b-debug-http-extract", kind="derived",
                  command="lines of a3's --debug stderr that carry the HTTP request/response summary (already masked)",
                  lines=keep)
    print(json.dumps({"exit": code, "extract": keep}, indent=1)[:12000])

elif phase == "after":
    common.az("a4-state-after", ["documentdb", "mongocluster", "show", "-g", RG, "-n", CL, "--query", STATE_QUERY, "-o", "json"])

elif phase == "poll":
    # show every 20 s until provisioningState is terminal and clusterStatus is not Updating, or time is up
    seconds = int(sys.argv[2])
    deadline = time.time() + seconds
    while True:
        rec, out, err, code = common.az(f"a4-poll-{int(time.time())}", ["documentdb", "mongocluster", "show", "-g", RG, "-n", CL,
                                                                        "--query", STATE_QUERY, "-o", "json"], quiet=True)
        st = rec.get("stdout_json") or {}
        print(json.dumps({"t": common.now_iso(), "exit": code, "serverVersion": st.get("serverVersion"),
                          "provisioningState": st.get("provisioningState"), "clusterStatus": st.get("clusterStatus"),
                          "lastModifiedAt": st.get("lastModifiedAt"), "stderr": (rec.get("stderr") or "")[:300]}))
        if code == 0 and st.get("provisioningState") in ("Succeeded", "Failed", "Canceled") and st.get("clusterStatus") != "Updating":
            break
        if time.time() > deadline:
            break
        time.sleep(20)

elif phase == "hello":
    warnings.simplefilter("ignore")
    import pymongo
    t0 = time.time()
    try:
        c = pymongo.MongoClient(common.ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000)
        h = c.admin.command("hello")
        res = {"ok": h.get("ok"), "maxWireVersion": h.get("maxWireVersion"), "minWireVersion": h.get("minWireVersion"),
               "msg": h.get("msg"), "internal": h.get("internal")}
        err = None
        c.close()
    except Exception as exc:
        res = None
        err = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    common.record(sys.argv[2] if len(sys.argv) > 2 else "a5-hello-after", kind="driver",
                  command="pymongo.MongoClient($MANAGED_URI, serverSelectionTimeoutMS=20000).admin.command('hello')",
                  pymongo_version=pymongo.version, duration_s=round(time.time() - t0, 2), response=res, error=err)
    print(json.dumps(common.mask({"response": res, "error": err}), indent=1, default=str))
elif phase == "buildinfo":
    warnings.simplefilter("ignore")
    import pymongo
    t0 = time.time()
    try:
        c = pymongo.MongoClient(common.ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000)
        b = c.admin.command("buildInfo")
        res = {k: b.get(k) for k in ("version", "versionArray", "gitVersion", "maxBsonObjectSize", "ok") if k in b}
        res["all_keys"] = sorted(b.keys())
        err = None
        c.close()
    except Exception as exc:
        res = None
        err = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    common.record(sys.argv[2] if len(sys.argv) > 2 else "a6-buildinfo-after", kind="driver",
                  command="pymongo.MongoClient($MANAGED_URI, serverSelectionTimeoutMS=20000).admin.command('buildInfo')",
                  pymongo_version=pymongo.version, duration_s=round(time.time() - t0, 2), response=res, error=err)
    print(json.dumps(common.mask({"response": res, "error": err}), indent=1, default=str))

elif phase == "activity":
    minutes = int(sys.argv[2])
    common.az(sys.argv[3] if len(sys.argv) > 3 else "a7-activity-log", ["monitor", "activity-log", "list", "--resource-group", RG, "--offset", f"{minutes}m",
                                  "--query", "[?contains(resourceId, 'ddb-samples-shared')].{time:eventTimestamp, "
                                             "op:operationName.value, status:status.value, subStatus:subStatus.value, "
                                             "httpStatus:properties.statusCode, statusMessage:properties.statusMessage, "
                                             "caller:caller, correlationId:correlationId}", "-o", "json"])
else:
    raise SystemExit(f"unknown phase {phase}")
