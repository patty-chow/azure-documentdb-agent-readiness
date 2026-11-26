"""Condensed view of report.json (exact errors, trimmed long successes) for the structured return."""
import json
import os

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
rep = json.load(open(os.path.join(TEST_DIR, "report.json")))
S = {s["id"]: s for s in rep["steps"]}


def j(x):
    return json.dumps(x, ensure_ascii=False, separators=(", ", ": "))


def cmd(*ids):
    out = []
    for i in ids:
        c = S[i]["command"]
        out.extend(c if isinstance(c, list) else [c])
    return " ;; ".join(out)


def err(e):
    keep = {k: e[k] for k in ("type", "name", "code", "codeName", "errmsg", "errorLabels", "errorLabels_in_reply", "message") if k in e}
    if "errmsg" not in keep and "message" not in keep and "str" in e:
        keep["str"] = e["str"]
    return keep


def pyop(sid, key=None):
    r = S[sid]["response"]
    if key:
        r = r[key]
    if r.get("ok"):
        return {"ok": True, "result": r.get("result")}
    return {"ok": False, "error": err(r["error"])}


def nodecase(sid):
    r = S[sid]["response"]
    out = {"driver": r["driver_version"], "callback_calls": len(r["callback_calls"])}
    first_err = None
    for st in r["steps"]:
        if st["ok"]:
            out[st["step"]] = "ok"
        else:
            e = err(st["error"])
            if first_err is not None and e == first_err[1]:
                out[st["step"]] = f"same error as {first_err[0]}"
            else:
                out[st["step"]] = e
                if first_err is None:
                    first_err = (st["step"], e)
        if st["ok"] and st["step"] == "ping":
            out["ping"] = st["result"]
        if st["ok"] and st["step"] == "find":
            out["find"] = f"{len(st['result'])} documents"
    return out


def azshort(sid, fields=None):
    r = S[sid]["response"]
    out = {"exit_code": r["exit_code"], "duration_s": r["duration_s"], "stderr": r.get("stderr")}
    js = r.get("stdout_json")
    if fields and isinstance(js, dict):
        p = js.get("properties", js)
        out["stdout_json (selected)"] = {f: p.get(f) for f in fields}
    else:
        out["stdout_json"] = js if js is not None else r.get("stdout")
    return out


steps = []


def add(step, command, response, reading):
    steps.append({"step": step, "command": command, "response": response if isinstance(response, str) else j(response), "reading": reading})


add("a1 authConfig before", cmd("a1"), azshort("a1"), S["a1"]["reading"])
add("a3 connection strings before", cmd("a3"), {"exit_code": 0, "connectionStrings": [{"name": c["name"], "connectionString": c["connectionString"]} for c in S["a3"]["response"]["stdout_json"]["connectionStrings"]]}, S["a3"]["reading"])
add("a4 hello saslSupportedMechs before (native client)", cmd("a4"),
    [{"call": c["name"], "saslSupportedMechs": c["response"]["saslSupportedMechs"], "maxWireVersion": c["response"]["maxWireVersion"]} for c in S["a4"]["response"]],
    S["a4"]["reading"])
add("a5 seed mt_entra.items over native auth", cmd("a5"), [{"call": c["name"], "response": c["response"]} for c in S["a5"]["response"]], S["a5"]["reading"])
add("a6a Entra token (claims subset)", cmd("a6a"), {k: v for k, v in S["a6a"]["response"]["result"]["claims_subset"].items() if k != "claim_names"} | {"expires_in_s": S["a6a"]["response"]["result"]["expires_in_s"]}, S["a6a"]["reading"])
add("a6b MONGODB-OIDC before Entra is enabled (PyMongo 4.20.2)", cmd("a6b"), {"ping": pyop("a6b", "ping"), "callback_calls": len(S["a6b"]["response"]["callback_calls"])}, S["a6b"]["reading"])
add("b0 CLI flag for authConfig", cmd("b0"), S["b0"]["response"]["excerpt_verbatim"].strip(), S["b0"]["reading"])
add("b1 enable MicrosoftEntraID alongside NativeAuth", cmd("b1"), azshort("b1", ["authConfig", "provisioningState", "clusterStatus"]), S["b1"]["reading"])
add("b2 state right after the update", cmd("b2"), azshort("b2"), S["b2"]["reading"] + " " + S["b3"]["reading"])
add("b4 native SCRAM ping after enabling", cmd("b4"), [c["response"] for c in S["b4"]["response"]], S["b4"]["reading"])
add("b5 hello saslSupportedMechs after enabling", cmd("b5"),
    [{"call": c["name"], "saslSupportedMechs": c["response"]["saslSupportedMechs"]} for c in S["b5"]["response"]], S["b5"]["reading"])
add("b6 MONGODB-OIDC after enabling, before registering the identity", cmd("b6"), {"ping": pyop("b6", "ping")}, S["b6"]["reading"])
c1 = S["c1"]["response"]["stdout"]
add("c1 az documentdb mongocluster --help", cmd("c1"), c1[c1.find("Subgroups:"):c1.find("Commands:")].strip(), S["c1"]["reading"])
c2 = S["c2"]["response"]["stdout"]
add("c2 microsoft-entra-user --help", cmd("c2"), c2[c2.find("Commands:"):].strip(), S["c2"]["reading"])
add("c3 microsoft-entra-user assign --help (verbatim parameters)", cmd("c3"),
    {"--type": S["c3"]["response"]["type_parameter_verbatim"], "--object-id": S["c3"]["response"]["object_id_parameter_verbatim"],
     "--role": S["c3"]["response"]["full_stdout"][S["c3"]["response"]["full_stdout"].find("    --role --roles"):S["c3"]["response"]["full_stdout"].find("    --type -t")].rstrip()},
    S["c3"]["reading"])
add("c4/c6 other help pages", cmd("c4-list", "c4-show", "c4-remove", "c6-firewall-rule", "c6-identity", "c6-replica"),
    {i: "exit " + str(S[i]["response"]["exit_code"]) for i in ("c4-list", "c4-show", "c4-remove", "c6-firewall-rule", "c6-identity", "c6-replica")} | {"identity group commands": "assign, list, remove, show, wait (cluster managed identities)"},
    "list/show/remove take the cluster, resource group and (show/remove) --object-id; firewall-rule, identity and replica do not manage Entra users.")
add("d1 signed-in identity object id", cmd("d1"), S["d1"]["response"], S["d1"]["reading"])
add("d1b account type", cmd("d1b"), azshort("d1b"), S["d1b"]["reading"])
add("d2 register the identity as administrator", cmd("d2"), {"exit_code": S["d2"]["response"]["exit_code"], "duration_s": S["d2"]["response"]["duration_s"], "stderr": S["d2"]["response"]["stderr"], "stdout_json (systemData omitted)": {k: v for k, v in S["d2"]["response"]["stdout_json"].items() if k != "systemData"}}, S["d2"]["reading"])
add("d3/d4 list and show", cmd("d3", "d4"),
    {"list names": [u["name"] for u in S["d3"]["response"]["stdout_json"]], "show properties": S["d4"]["response"]["stdout_json"]["properties"]},
    S["d3"]["reading"] + " " + S["d4"]["reading"])
add("d5 ARM REST users list", cmd("d5"), {"value[1].properties": S["d5"]["response"]["stdout_json"]["value"][1]["properties"],
                                         "value[0].properties": S["d5"]["response"]["stdout_json"]["value"][0]["properties"]}, S["d5"]["reading"])
add("d6 first MONGODB-OIDC attempt after registration", cmd("d6"), {"started_at": S["d6"]["response"]["started_at"], "ping": pyop("d6", "ping"), "find": pyop("d6", "find")}, S["d6"]["reading"])
d7 = S["d7"]["response"]
add("d7 native admin view of the Entra user", cmd("d7"),
    {"usersInfo <object-id>": d7[2]["response"], "usersInfo 1 user names": [u["user"] for u in d7[0]["response"]["users"]]}, S["d7"]["reading"])
add("e0 throwaway venvs", cmd("e0"), {k: {kk: vv for kk, vv in v.items() if kk != "pip_log"} for k, v in S["e0"]["response"]["resolved"].items()} | {"exit_codes": [0, 0, 0]}, S["e0"]["reading"])
add("e1 PyMongo 4.6.3: import Learn's API", cmd("e1-import_oidc_callback_api"), pyop("e1-import_oidc_callback_api"), S["e1-import_oidc_callback_api"]["reading"])
add("e1 PyMongo 4.6.3: OIDC_CALLBACK", cmd("e1-construct-OIDC_CALLBACK"), pyop("e1-construct-OIDC_CALLBACK"), S["e1-construct-OIDC_CALLBACK"]["reading"])
add("e1 PyMongo 4.6.3: pre-GA request_token_callback, default hosts", cmd("e1-request_token_callback_default_hosts-ping"),
    {"construct": "ok", "ping": pyop("e1-request_token_callback_default_hosts-ping", "ping")}, S["e1-request_token_callback_default_hosts-ping"]["reading"])
add("e1 PyMongo 4.6.3: pre-GA request_token_callback, allowed_hosts", cmd("e1-request_token_callback_allowed_hosts-ping"),
    {"construct": "ok", "ping": pyop("e1-request_token_callback_allowed_hosts-ping", "ping"), "traceback_tail": S["e1-request_token_callback_allowed_hosts-ping"]["response"]["ping"]["traceback_tail"][0].strip()},
    S["e1-request_token_callback_allowed_hosts-ping"]["reading"])
add("e2 PyMongo 4.7.0: Learn's callback as written", cmd("e2"), {"ping": pyop("e2", "ping"), "find": pyop("e2", "find"), "callback_calls": 0}, S["e2"]["reading"])
add("e2b/e2c PyMongo 4.7.0 with ALLOWED_HOSTS", S["e2b"]["command"][0] + " ;; ping ;; find ;; insert_one ;; and the same client with 'ALLOWED_HOSTS': ['*.mongocluster.cosmos.azure.com']: ping ;; find",
    {"['*.azure.com']": {k: pyop("e2b", k) for k in ("ping", "insert_one")} | {"find": f"{len(S['e2b']['response']['find']['result'])} documents"},
     "['*.mongocluster.cosmos.azure.com']": {"ping": pyop("e2c", "ping"), "find": f"{len(S['e2c']['response']['find']['result'])} documents"}},
    S["e2b"]["reading"] + " " + S["e2c"]["reading"])
add("e3 PyMongo 4.20.2 (latest): Learn's callback as written", cmd("e3"),
    {"ping": pyop("e3", "ping"), "find": S["e3"]["response"]["find"]["result"], "insert_one": pyop("e3", "insert_one"),
     "callback_context": S["e3"]["response"]["callback_calls"][0]["context"]}, S["e3"]["reading"])
cs = S["e3-connectionStatus_showPrivileges"]["response"]["result"]
add("e3 connectionStatus showPrivileges / plain", cmd("e3-connectionStatus_showPrivileges", "e3-connectionStatus"),
    {"showPrivileges": {"authenticatedUsers": cs["authInfo"]["authenticatedUsers"], "authenticatedUserRoles": cs["authInfo"]["authenticatedUserRoles"],
                        "authenticatedUserPrivileges (summary; full list in report.json)": [{"resource": p["resource"], "actions": len(p["actions"])} for p in cs["authInfo"]["authenticatedUserPrivileges"]]},
     "plain": S["e3-connectionStatus"]["response"]["result"]},
    S["e3-connectionStatus_showPrivileges"]["reading"] + " " + S["e3-connectionStatus"]["reading"])
ui = {}
for k in ("usersInfo_oid_admin", "usersInfo_userdoc_admin", "usersInfo_external_db", "usersInfo_userdoc_external", "usersInfo_oid_showPrivileges", "usersInfo_1", "usersInfo_forAllDBs"):
    r = S["e3-" + k]["response"]
    if r["ok"]:
        users = r["result"]["users"]
        if k == "usersInfo_oid_showPrivileges":
            ui[k] = {"keys": list(users[0].keys()), "inheritedPrivileges entries": len(users[0]["inheritedPrivileges"])}
        elif k in ("usersInfo_1", "usersInfo_forAllDBs"):
            ui[k] = [u["_id"] for u in users]
        elif k == "usersInfo_oid_admin":
            ui[k] = r["result"]
        else:
            ui[k] = "same users document as usersInfo_oid_admin" if r["result"] == S["e3-usersInfo_oid_admin"]["response"]["result"] else r["result"]
    else:
        ui[k] = {"error": err(r["error"])}
add("e3 usersInfo on the identity", cmd(*("e3-" + k for k in ui)), ui,
    "usersInfo returns the identity in db admin with customData.IdentityProvider; a $external user document is rejected with 2 BadValue, while running the command on the $external database works.")
add("e3b PyMongo 4.20.2 on the .global. host", cmd("e3b"), {"ping": pyop("e3b", "ping"), "find": pyop("e3b", "find")["ok"]}, S["e3b"]["reading"])
add("e4 ALLOWED_HOSTS check across PyMongo releases (source)", cmd("e4"), S["e4"]["response"], S["e4"]["reading"])
add("e5 live check PyMongo 4.10.1 vs 4.11 (no ALLOWED_HOSTS)", cmd("e5-4.10.1", "e5-4.11"),
    {"4.10.1": {"ping": pyop("e5-4.10.1", "ping")}, "4.11": {"ping": pyop("e5-4.11", "ping"), "find_ok": S["e5-4.11"]["response"]["find"]["ok"]}},
    S["e5-4.10.1"]["reading"] + " " + S["e5-4.11"]["reading"])
add("f0 npm install", cmd("f0"), {k: v for k, v in S["f0"]["response"].items()}, S["f0"]["reading"])
add("f1-f3 Node 6.6.0 with OIDC_CALLBACK (['*.azure.com'], ['*.mongocluster.cosmos.azure.com'], none)", cmd("f1") + " (and the same with the other two ALLOWED_HOSTS settings)",
    {"f1": nodecase("f1"), "f2": ("same as f1" if nodecase("f2") == nodecase("f1") else nodecase("f2")), "f3": ("same as f1" if nodecase("f3") == nodecase("f1") else nodecase("f3"))}, S["f1"]["reading"] + " " + S["f2"]["reading"])
add("f4 Node 6.6.0 pre-GA REQUEST_TOKEN_CALLBACK", cmd("f4"), nodecase("f4"), S["f4"]["reading"])
add("f5/f6 Node 6.7.0 with ALLOWED_HOSTS ['*.azure.com'] and ['*.mongocluster.cosmos.azure.com']", cmd("f5") + " (and with ['*.mongocluster.cosmos.azure.com'])",
    {"f5": nodecase("f5"), "f6": nodecase("f6"), "callback params": S["f5"]["response"]["callback_calls"][0]["paramKeys"]}, S["f5"]["reading"] + " " + S["f6"]["reading"])
add("f7 Node 6.7.0 without ALLOWED_HOSTS", cmd("f7"), nodecase("f7"), S["f7"]["reading"])
add("f9/f10/f13 Node 7.9.1 (latest) with both patterns and on the .global. host", cmd("f9") + " (and with ['*.mongocluster.cosmos.azure.com'] on the plain and .global. hosts)",
    {"f9": nodecase("f9"), "f10": nodecase("f10"), "f13": nodecase("f13")}, S["f9"]["reading"] + " " + S["f10"]["reading"] + " " + S["f13"]["reading"])
add("f11 Node 7.9.1 without ALLOWED_HOSTS", cmd("f11"), nodecase("f11"), S["f11"]["reading"])
add("f8/f12 Learn's TypeScript expiresInSeconds formula", cmd("f8") + " (and the same on 7.9.1)",
    {"6.7.0": nodecase("f8") | {"expiresInSeconds": S["f8"]["response"]["callback_calls"][0]["expiresInSeconds"]},
     "7.9.1": nodecase("f12") | {"expiresInSeconds": S["f12"]["response"]["callback_calls"][0]["expiresInSeconds"]}},
    S["f8"]["reading"] + " " + S["f12"]["reading"])
add("g1 raw MONGODB-OIDC saslStart without a token", cmd("g1"), [{"call": c["name"], "error": c["error"]} for c in S["g1"]["response"]], S["g1"]["reading"])
add("z1 authConfig after", cmd("z1"), azshort("z1"), S["z1"]["reading"])
add("z3 connection strings after", cmd("z3"), {"exit_code": 0, "connectionStrings": [({"name": c["name"], "description": c["description"], "connectionString": c["connectionString"]} if "OIDC" in c["connectionString"] else {"name": c["name"], "unchanged": True}) for c in S["z3"]["response"]["stdout_json"]["connectionStrings"]]}, S["z3"]["reading"])
add("y1 drop mt_entra", cmd("y1"), [{"call": c["name"], "response": c["response"]} for c in S["y1"]["response"]], S["y1"]["reading"])
add("y2 delete venvs and node_modules", cmd("y2"), S["y2"]["response"], S["y2"]["reading"])

out = {"test": "m-entra", "steps": steps, "conclusions": rep["conclusions"], "config_changes": rep["config_changes"],
       "script_path": os.path.join(TEST_DIR, "report.json")}
with open(os.path.join(TEST_DIR, "raw", "structured_compact.json"), "w") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)
print(len(steps), "steps", len(json.dumps(out)), "chars")

# --- abbreviate repeated client constructor strings ---------------------------------------
import re  # noqa: E402

p = os.path.join(TEST_DIR, "raw", "structured_compact.json")
d = json.load(open(p))
PY_BASE = "MongoClient('mongodb+srv://ddb-samples-shared.mongocluster.cosmos.azure.com/', connectTimeoutMS=120000, serverSelectionTimeoutMS=20000, tls=True, retryWrites=False, maxIdleTimeMS=120000, authMechanism='MONGODB-OIDC', authMechanismProperties="
NODE_BASE_RE = re.compile(r"new MongoClient\('mongodb\+srv://ddb-samples-shared\.(global\.)?mongocluster\.cosmos\.azure\.com/', \{ connectTimeoutMS: 120000, serverSelectionTimeoutMS: 20000, tls: true, retryWrites: false, maxIdleTimeMS: 120000, authMechanism: 'MONGODB-OIDC', authMechanismProperties: (.*?) \}\); await client\.connect\(\); await client\.db\('admin'\)\.command\(\{ ping: 1 \}\); await client\.db\('mt_entra'\)\.collection\('items'\)\.find\(\{\}, \{ projection: \{ _id: 0 \} \}\)\.sort\(\{ n: 1 \}\)\.toArray\(\)")
state = {"py": False, "node": False}
for s_ in d["steps"]:
    c = s_["command"]
    if PY_BASE in c:
        if state["py"]:
            c = c.replace(PY_BASE, "PYCLIENT(authMechanismProperties=")
        state["py"] = True

    def node_sub(m):
        host = "global" if m.group(1) else "plain"
        if not state["node"]:
            state["node"] = True
            return m.group(0)
        return f"NODECALL[{host} host](authMechanismProperties: {m.group(2)})"
    s_["command"] = NODE_BASE_RE.sub(node_sub, c)
d["notes_on_commands"] = ("PYCLIENT(...) abbreviates " + PY_BASE + "...) with the stated authMechanismProperties (serverSelectionTimeoutMS 30000 in the a6/b6 probes, 15000 in d6); "
                          "NODECALL[host](...) abbreviates the full Node call shown in the first Node step, with the stated authMechanismProperties and host.")
json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
print("abbreviated; total chars", len(json.dumps(d)))
