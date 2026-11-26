"""Native-auth (SCRAM) helper for m-entra. Run with the project venv python -I.

Usage: python -I native.py <action> <step_id>
  actions: hello_mechs, seed, admin_usersinfo, drop, ping
Appends masked records to raw/steps.jsonl. Never prints the URI or password.
"""
import json
import sys
import time
import warnings

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

warnings.simplefilter("ignore")  # CosmosDB UserWarning is not part of this test
from pymongo import MongoClient  # noqa: E402
import pymongo  # noqa: E402

DB = "mt_entra"
action, step_id = sys.argv[1], sys.argv[2]
OID = common.IDS["oid"]
ADMIN_USER = "factoryadmin"


def jsonable(x):
    return json.loads(json.dumps(x, default=lambda o: repr(o)))


def err_info(e):
    d = {"type": f"{type(e).__module__}.{type(e).__name__}", "str": str(e)}
    if getattr(e, "code", None) is not None:
        d["code"] = e.code
    det = getattr(e, "details", None)
    if isinstance(det, dict):
        d["codeName"] = det.get("codeName")
        d["errmsg"] = det.get("errmsg")
        if "errorLabels" in det:
            d["errorLabels"] = det["errorLabels"]
        d["details"] = det
    return d


client = MongoClient(common.ENV["MANAGED_URI"], serverSelectionTimeoutMS=30000, appname="m-entra-native")
URI_DISPLAY = "MongoClient($MANAGED_URI)  # mongodb+srv://factoryadmin:<password>@<plain host>/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
calls = []


def do(name, display, fn):
    t0 = time.time()
    rec = {"call": display, "client": URI_DISPLAY}
    try:
        rec["response"] = jsonable(fn())
        rec["ok"] = True
    except Exception as e:  # noqa: BLE001
        rec["ok"] = False
        rec["error"] = err_info(e)
    rec["duration_s"] = round(time.time() - t0, 3)
    calls.append({"name": name, **rec})


if action == "hello_mechs":
    for user in (f"admin.{ADMIN_USER}", f"admin.{OID}", f"$external.{OID}"):
        disp_user = user.replace(OID, "<object-id>")
        do(f"hello saslSupportedMechs {disp_user}",
           f"client.admin.command({{'hello': 1, 'saslSupportedMechs': '{disp_user}'}})",
           lambda u=user: {k: v for k, v in client.admin.command({"hello": 1, "saslSupportedMechs": u}).items()
                           if k in ("saslSupportedMechs", "maxWireVersion", "msg", "internal", "ok", "isWritablePrimary")})
elif action == "seed":
    do("drop collection (idempotent)", f"client['{DB}']['items'].drop()", lambda: client[DB]["items"].drop())
    do("insert_many", f"client['{DB}']['items'].insert_many([{{'n': 1, 'src': 'native-seed'}}, {{'n': 2, 'src': 'native-seed'}}])",
       lambda: {"inserted": len(client[DB]["items"].insert_many([{"n": 1, "src": "native-seed"}, {"n": 2, "src": "native-seed"}]).inserted_ids)})
elif action == "admin_usersinfo":
    do("usersInfo 1 (native admin)", "client.admin.command({'usersInfo': 1})", lambda: client.admin.command({"usersInfo": 1}))
    do("usersInfo forAllDBs (native admin)", "client.admin.command({'usersInfo': {'forAllDBs': True}})",
       lambda: client.admin.command({"usersInfo": {"forAllDBs": True}}))
    do("usersInfo <object-id> (native admin)", "client.admin.command({'usersInfo': '<object-id>'})",
       lambda: client.admin.command({"usersInfo": OID}))
    do("usersInfo <object-id> showPrivileges (native admin)", "client.admin.command({'usersInfo': '<object-id>', 'showPrivileges': True})",
       lambda: client.admin.command({"usersInfo": OID, "showPrivileges": True}))
    do("connectionStatus showPrivileges (native admin)", "client.admin.command({'connectionStatus': 1, 'showPrivileges': True})",
       lambda: client.admin.command({"connectionStatus": 1, "showPrivileges": True}))
elif action == "ping":
    do("ping (native SCRAM)", "client.admin.command('ping')", lambda: client.admin.command("ping"))
elif action == "drop":
    do("dropDatabase", f"client.drop_database('{DB}')", lambda: client.drop_database(DB))
    do("listDatabases filter", f"client.admin.command({{'listDatabases': 1, 'nameOnly': True, 'filter': {{'name': '{DB}'}}}})",
       lambda: client.admin.command({"listDatabases": 1, "nameOnly": True, "filter": {"name": DB}}))
else:
    raise SystemExit(f"unknown action {action}")

client.close()
rec = common.record(step_id, kind="driver", driver=f"pymongo {pymongo.version}", action=action, calls=calls)
print(json.dumps({"id": step_id, "calls": [(c["name"], c["ok"], (c.get("error") or {}).get("codeName") or (c.get("error") or {}).get("str", "")[:150] if not c["ok"] else str(c.get("response"))[:300]) for c in rec["calls"]]}, indent=1))
