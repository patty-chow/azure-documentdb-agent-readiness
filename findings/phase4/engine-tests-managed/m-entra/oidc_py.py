"""MONGODB-OIDC probe for one PyMongo version (run with that venv's python -I).

Usage: python -I oidc_py.py --label <label> --mode probe|full|legacy [--host plain|global]
Writes one masked JSON object to raw/oidc_py_<label>.json and prints a short masked summary.
Never prints or stores the access token.
"""
import argparse
import base64
import json
import os
import platform
import sys
import time
import traceback
import warnings

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

SCOPE = "https://ossrdbms-aad.database.windows.net/.default"
DB = "mt_entra"
AZURE_CLI_APP_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # public, well-known first-party app id

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--mode", default="full", choices=["probe", "full", "legacy"])
ap.add_argument("--host", default="plain", choices=["plain", "global"])
ap.add_argument("--sst", type=int, default=30000, help="serverSelectionTimeoutMS")
ap.add_argument("--allowed-hosts", default=None, help="comma-separated ALLOWED_HOSTS to add to authMechanismProperties")
args = ap.parse_args()

HOST = common.ENV["MANAGED_HOST"] if args.host == "plain" else common.ENV["MANAGED_GLOBAL_HOST"]
OID = common.IDS["oid"]
out = {"label": args.label, "mode": args.mode, "host_form": args.host, "host": HOST,
       "started_at": common.now_iso(), "python": platform.python_version(), "steps": []}
caught_warnings = []
warnings.simplefilter("always")
_orig_showwarning = warnings.showwarning


def _showwarning(message, category, filename, lineno, file=None, line=None):
    caught_warnings.append(f"{category.__name__}: {message}")


warnings.showwarning = _showwarning


def err_info(e, depth=0):
    d = {"type": f"{type(e).__module__}.{type(e).__name__}", "str": str(e)}
    code = getattr(e, "code", None)
    if code is not None:
        d["code"] = code
    details = getattr(e, "details", None)
    if isinstance(details, dict):
        d["details"] = {k: v for k, v in details.items() if k not in ("$clusterTime",)}
        d["codeName"] = details.get("codeName")
        d["errmsg"] = details.get("errmsg")
        if "errorLabels" in details:
            d["errorLabels"] = details.get("errorLabels")
    labels = getattr(e, "_error_labels", None)
    if labels:
        d["errorLabels_driver"] = sorted(labels)
    if e.__cause__ is not None and depth < 3:
        d["cause"] = err_info(e.__cause__, depth + 1)
    elif e.__context__ is not None and depth < 3 and not isinstance(e.__context__, KeyboardInterrupt):
        d["context"] = err_info(e.__context__, depth + 1)
    return d


def step(name, call, fn):
    t0 = time.time()
    rec = {"step": name, "call": call}
    try:
        res = fn()
        rec["ok"] = True
        rec["result"] = res
    except Exception as e:  # noqa: BLE001
        rec["ok"] = False
        rec["error"] = err_info(e)
        rec["traceback_tail"] = traceback.format_exc().strip().splitlines()[-3:]
    rec["duration_s"] = round(time.time() - t0, 3)
    out["steps"].append(rec)
    return rec


def jsonable(x):
    return json.loads(json.dumps(x, default=lambda o: repr(o)))


# --- versions ---------------------------------------------------------------
import pymongo  # noqa: E402

out["pymongo"] = pymongo.version
try:
    import azure.identity as azid
    out["azure_identity"] = getattr(azid, "__version__", None) or __import__("azure.identity._version", fromlist=["VERSION"]).VERSION
except Exception as e:  # noqa: BLE001
    out["azure_identity"] = repr(e)
from azure.identity import AzureCliCredential  # noqa: E402

credential = AzureCliCredential()


# --- token (claims subset only) ----------------------------------------------
def _token_info():
    t0 = time.time()
    tok = credential.get_token(SCOPE)
    dt = round(time.time() - t0, 2)
    part = tok.token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    return {
        "acquired": True,
        "get_token_s": dt,
        "expires_in_s": int(tok.expires_on - time.time()),
        "claims_subset": {
            "aud": claims.get("aud"),
            "ver": claims.get("ver"),
            "idp": claims.get("idp"),
            "acct": claims.get("acct"),
            "amr": claims.get("amr"),
            "scp": claims.get("scp"),
            "iss_is_sts_windows_net_for_tenant": claims.get("iss") == f"https://sts.windows.net/{common.IDS['tenant']}/",
            "tid_matches_signed_in_tenant": claims.get("tid") == common.IDS["tenant"],
            "oid_matches_signed_in_user": claims.get("oid") == OID,
            "appid_is_azure_cli": claims.get("appid") == AZURE_CLI_APP_ID,
            "claim_names": sorted(claims.keys()),
        },
    }


step("token", "AzureCliCredential().get_token('https://ossrdbms-aad.database.windows.net/.default') (claims subset only)", _token_info)

# --- callback API presence -----------------------------------------------------
callback_calls = []
def _import_api():
    from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult  # noqa: F401
    return "imported"


have_new_api = step("import_oidc_callback_api",
                    "from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult",
                    _import_api)["ok"]

if have_new_api:
    from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult  # noqa: E402

    class AzureIdentityTokenCallback(OIDCCallback):
        def __init__(self, cred):
            self.credential = cred

        def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
            ctx = {}
            for k, v in vars(context).items():
                if k == "refresh_token":
                    ctx[k] = None if v is None else "<present>"
                else:
                    ctx[k] = v if isinstance(v, (int, float, str, type(None), bool)) else repr(v)
            callback_calls.append({"at": common.now_iso(), "context": ctx})
            token = self.credential.get_token(SCOPE).token
            return OIDCCallbackResult(access_token=token)
else:
    class AzureIdentityTokenCallback:  # same shape as Learn's class, without the missing base class
        def __init__(self, cred):
            self.credential = cred

        def fetch(self, context):
            callback_calls.append({"at": common.now_iso(), "context": repr(context)})
            token = self.credential.get_token(SCOPE).token
            return {"access_token": token}

from pymongo import MongoClient  # noqa: E402


def construct(holder, props, label):
    holder["c"] = make_client(props, label)
    return "constructed"


def make_client(props, label):
    return MongoClient(
        f"mongodb+srv://{HOST}/",
        connectTimeoutMS=120000,
        serverSelectionTimeoutMS=args.sst,
        tls=True,
        retryWrites=False,
        maxIdleTimeMS=120000,
        authMechanism="MONGODB-OIDC",
        authMechanismProperties=props,
        appname=f"m-entra-{label}",
    )


CONSTRUCT_CALL = ("MongoClient('mongodb+srv://%s/', connectTimeoutMS=120000, serverSelectionTimeoutMS=%d, tls=True, "
                  "retryWrites=False, maxIdleTimeMS=120000, authMechanism='MONGODB-OIDC', "
                  "authMechanismProperties=%s)")


def exercise(client, tag, full):
    step(f"{tag}:ping", "client.admin.command('ping')", lambda: jsonable(client.admin.command("ping")))
    step(f"{tag}:find", f"list(client['{DB}']['items'].find({{}}, {{'_id': 0}}).sort('n', 1))",
         lambda: jsonable(list(client[DB]["items"].find({}, {"_id": 0}).sort("n", 1))))
    if not full:
        return
    step(f"{tag}:insert_one", f"client['{DB}']['items'].insert_one({{'n': 100, 'src': 'oidc-{args.label}'}})",
         lambda: {"acknowledged": client[DB]["items"].insert_one({"n": 100, "src": f"oidc-{args.label}"}).acknowledged})
    step(f"{tag}:find_after_insert", f"list(client['{DB}']['items'].find({{'n': 100}}, {{'_id': 0}}))",
         lambda: jsonable(list(client[DB]["items"].find({"n": 100}, {"_id": 0}))))
    step(f"{tag}:connectionStatus_showPrivileges", "client.admin.command({'connectionStatus': 1, 'showPrivileges': True})",
         lambda: jsonable(client.admin.command({"connectionStatus": 1, "showPrivileges": True})))
    step(f"{tag}:connectionStatus", "client.admin.command({'connectionStatus': 1})",
         lambda: jsonable(client.admin.command({"connectionStatus": 1})))
    step(f"{tag}:usersInfo_oid_admin", "client.admin.command({'usersInfo': '<object-id>'})",
         lambda: jsonable(client.admin.command({"usersInfo": OID})))
    step(f"{tag}:usersInfo_userdoc_admin", "client.admin.command({'usersInfo': {'user': '<object-id>', 'db': 'admin'}})",
         lambda: jsonable(client.admin.command({"usersInfo": {"user": OID, "db": "admin"}})))
    step(f"{tag}:usersInfo_userdoc_external", "client.admin.command({'usersInfo': {'user': '<object-id>', 'db': '$external'}})",
         lambda: jsonable(client.admin.command({"usersInfo": {"user": OID, "db": "$external"}})))
    step(f"{tag}:usersInfo_external_db", "client['$external'].command({'usersInfo': '<object-id>'})",
         lambda: jsonable(client["$external"].command({"usersInfo": OID})))
    step(f"{tag}:usersInfo_oid_showPrivileges", "client.admin.command({'usersInfo': '<object-id>', 'showPrivileges': True})",
         lambda: jsonable(client.admin.command({"usersInfo": OID, "showPrivileges": True})))
    step(f"{tag}:usersInfo_1", "client.admin.command({'usersInfo': 1})",
         lambda: jsonable(client.admin.command({"usersInfo": 1})))
    step(f"{tag}:usersInfo_forAllDBs", "client.admin.command({'usersInfo': {'forAllDBs': True}})",
         lambda: jsonable(client.admin.command({"usersInfo": {"forAllDBs": True}})))
    step(f"{tag}:listDatabases_nameOnly", "client.admin.command({'listDatabases': 1, 'nameOnly': True})",
         lambda: jsonable(client.admin.command({"listDatabases": 1, "nameOnly": True})))


if args.mode in ("probe", "full"):
    props = {"OIDC_CALLBACK": AzureIdentityTokenCallback(credential)}
    props_disp = "{'OIDC_CALLBACK': AzureIdentityTokenCallback(AzureCliCredential())}"
    if args.allowed_hosts:
        props["ALLOWED_HOSTS"] = args.allowed_hosts.split(",")
        props_disp = "{'OIDC_CALLBACK': AzureIdentityTokenCallback(AzureCliCredential()), 'ALLOWED_HOSTS': %r}" % props["ALLOWED_HOSTS"]
    out["allowed_hosts"] = props.get("ALLOWED_HOSTS")
    holder = {}
    r = step("construct:OIDC_CALLBACK", CONSTRUCT_CALL % (HOST, args.sst, props_disp),
             lambda: construct(holder, props, args.label))
    if r["ok"]:
        exercise(holder["c"], "OIDC_CALLBACK", args.mode == "full")
        holder["c"].close()

if args.mode == "legacy":
    # 4.6.x pre-GA API: a plain function with two parameters (idp_info, context) returning a dict.
    def request_token_callback(idp_info, context):
        ctx = {k: (None if k == "refresh_token" and v is None else ("<present>" if k == "refresh_token" else v)) for k, v in dict(context).items()}
        callback_calls.append({"at": common.now_iso(), "idp_info": idp_info, "context": ctx})
        return {"access_token": credential.get_token(SCOPE).token}

    # (1) Learn's OIDC_CALLBACK shape on this version
    props = {"OIDC_CALLBACK": AzureIdentityTokenCallback(credential)}
    holder = {}
    r = step("construct:OIDC_CALLBACK", CONSTRUCT_CALL % (HOST, args.sst, "{'OIDC_CALLBACK': AzureIdentityTokenCallback(AzureCliCredential())}"),
             lambda: construct(holder, props, args.label))
    if r["ok"]:
        exercise(holder["c"], "OIDC_CALLBACK", False)
        holder["c"].close()
    # (2) pre-GA request_token_callback with the default allowed_hosts
    holder = {}
    r = step("construct:request_token_callback_default_hosts",
             CONSTRUCT_CALL % (HOST, args.sst, "{'request_token_callback': request_token_callback}"),
             lambda: construct(holder, {"request_token_callback": request_token_callback}, args.label))
    if r["ok"]:
        exercise(holder["c"], "request_token_callback_default_hosts", False)
        holder["c"].close()
    # (3) pre-GA request_token_callback with allowed_hosts for the Azure domain
    holder = {}
    r = step("construct:request_token_callback_allowed_hosts",
             CONSTRUCT_CALL % (HOST, args.sst, "{'request_token_callback': request_token_callback, 'allowed_hosts': ['*.mongocluster.cosmos.azure.com']}"),
             lambda: construct(holder, {"request_token_callback": request_token_callback,
                                                         "allowed_hosts": ["*.mongocluster.cosmos.azure.com"]}, args.label))
    if r["ok"]:
        exercise(holder["c"], "request_token_callback_allowed_hosts", False)
        holder["c"].close()

out["callback_calls"] = callback_calls
out["warnings"] = sorted(set(caught_warnings))
out["finished_at"] = common.now_iso()
masked = common.mask(jsonable(out))
path = os.path.join(common.RAW_DIR, f"oidc_py_{args.label}.json")
with open(path, "w") as fh:
    json.dump(masked, fh, indent=1)
summary = [(s["step"], "ok" if s["ok"] else (s["error"].get("type", "") + " " + str(s["error"].get("code", "")) + " " + (s["error"].get("str", "")[:160]))) for s in masked["steps"]]
print(json.dumps({"label": args.label, "pymongo": masked["pymongo"], "file": path, "summary": summary,
                  "callback_calls": len(callback_calls)}, indent=1))
