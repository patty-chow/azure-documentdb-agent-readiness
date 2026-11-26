"""Like-for-like with the open-source parity test 00f2: unauthenticated MONGODB-OIDC saslStart, empty payload."""
import json
import sys
import time
import warnings

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

warnings.simplefilter("ignore")
import bson  # noqa: E402
import pymongo  # noqa: E402
from bson import Binary  # noqa: E402
from pymongo import MongoClient  # noqa: E402

host = common.ENV["MANAGED_HOST"]
client = MongoClient(f"mongodb+srv://{host}/?tls=true&retrywrites=false", serverSelectionTimeoutMS=20000)
calls = []
for name, payload in (("empty payload", {}), ("principal-only payload {n: <object-id>}", {"n": common.IDS["oid"]})):
    t0 = time.time()
    rec = {"name": name,
           "call": f"MongoClient('mongodb+srv://{host}/?tls=true&retrywrites=false')['admin'].command({{'saslStart': 1, 'mechanism': 'MONGODB-OIDC', 'payload': Binary(bson.encode({json.dumps(payload).replace(common.IDS['oid'], '<object-id>')}))}})  # unauthenticated client, no token"}
    try:
        rec["response"] = json.loads(json.dumps(client.admin.command({"saslStart": 1, "mechanism": "MONGODB-OIDC", "payload": Binary(bson.encode(payload))}), default=repr))
        rec["ok"] = True
    except pymongo.errors.OperationFailure as e:
        rec["ok"] = False
        rec["error"] = {"type": type(e).__name__, "code": e.code, "codeName": (e.details or {}).get("codeName"),
                        "errmsg": (e.details or {}).get("errmsg"), "errorLabels_in_reply": (e.details or {}).get("errorLabels"),
                        "reply": e.details}
    rec["duration_s"] = round(time.time() - t0, 3)
    calls.append(rec)
client.close()
r = common.record("g1-raw-saslStart-MONGODB-OIDC", kind="driver", driver=f"pymongo {pymongo.version}", calls=calls)
print(json.dumps(r["calls"], indent=1))
