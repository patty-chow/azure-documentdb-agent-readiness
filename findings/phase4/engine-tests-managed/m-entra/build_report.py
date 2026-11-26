"""Assemble report.json for m-entra from the masked raw records. Run with the project venv python -I."""
import json
import os
import sys

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

RAW = common.RAW_DIR
recs = {}
for line in open(os.path.join(RAW, "steps.jsonl")):
    r = json.loads(line)
    recs[r["id"]] = r  # last record per id wins (help texts were re-recorded once)


def py(label):
    return json.load(open(os.path.join(RAW, f"oidc_py_{label}.json")))


node = json.load(open(os.path.join(RAW, "oidc_node.json")))
nruns = {r["label"]: r for r in node["runs"]}


def azresp(r):
    out = {"exit_code": r.get("exit_code"), "duration_s": r.get("duration_s")}
    if r.get("stdout_json") is not None:
        out["stdout_json"] = r["stdout_json"]
    elif r.get("stdout") is not None:
        out["stdout"] = r["stdout"]
    out["stderr"] = r.get("stderr")
    return out


def help_excerpt(r, start, stop=None):
    txt = r.get("stdout") or ""
    i = txt.find(start)
    if i < 0:
        return txt
    j = txt.find(stop, i + len(start)) if stop else -1
    return txt[i:j] if j > 0 else txt[i:]


def pystep(label, name):
    for s in py(label)["steps"]:
        if s["step"] == name:
            d = {"ok": s["ok"], "duration_s": s["duration_s"]}
            if s["ok"]:
                d["result"] = s.get("result")
            else:
                e = s["error"]
                d["error"] = {k: e.get(k) for k in ("type", "code", "codeName", "errmsg", "errorLabels", "str") if e.get(k) is not None}
                if "errorLabels" not in e and e.get("details") is not None:
                    d["error"]["errorLabels_in_reply"] = None
                if s.get("traceback_tail"):
                    d["traceback_tail"] = s["traceback_tail"]
            return s["call"], d
    raise KeyError((label, name))


def nodestep(label):
    r = nruns[label]
    return r["call"], {"driver_version": r["driver_version"], "steps": r["steps"],
                       "callback_calls": r["callback_calls"]}


def callrec(r, name):
    for c in r["calls"]:
        if c["name"] == name:
            return c
    raise KeyError(name)


steps = []


def add(sid, step, command, response, reading, vs="n/a", os_ref=None):
    d = {"id": sid, "step": step, "command": command, "response": response, "reading": reading, "vs_open_source": vs}
    if os_ref:
        d["open_source_reference"] = os_ref
    steps.append(d)


OS_PARITY = "findings/phase4/engine-tests-1.2/local-gateway-parity/report.json (documentdb-local pg17-1.2.0)"

# ---------------------------------------------------------------- (a) before
r = recs["a1-authConfig-before"]
add("a1", "Record properties.authConfig before the change", r["command"], azresp(r),
    "Before the test the cluster allowed only native (SCRAM) authentication: allowedModes was [\"NativeAuth\"].")
r = recs["a2-show-before"]
add("a2", "Full cluster resource before the change (masked)", r["command"], azresp(r),
    "The cluster was Ready/Succeeded, M30, serverVersion 8.0, identity type None, previewFeatures [FullTextSearch] (left by m-fts), lastModifiedAt 2026-11-25T21:50:26Z.")
r = recs["a3-connection-strings-before"]
add("a3", "Connection strings before the change", r["command"], azresp(r),
    "With NativeAuth only, list-connection-strings returned just the two SCRAM-SHA-256 strings (GlobalReadWrite and Self).")
r = recs["a4-hello-saslSupportedMechs-before"]
add("a4", "hello saslSupportedMechs before enabling Entra (native SCRAM client, pymongo 4.20.1)",
    [c["call"] + "   # client: " + c["client"] for c in r["calls"]], r["calls"],
    "Before enabling Entra, hello returned saslSupportedMechs ['SCRAM-SHA-256'] for the native admin, for admin.<object-id> and for $external.<object-id> alike, which is the same static list the open-source 1.2.0 gateway returns for any user.",
    "same", OS_PARITY + " steps 00e/00f: saslSupportedMechs ['SCRAM-SHA-256'] for admin.testadmin and for an unknown user")
r = recs["a5-seed-native"]
add("a5", "Seed mt_entra.items with two documents over native auth", [c["call"] for c in r["calls"]], r["calls"],
    "Two documents (n 1 and 2) were inserted with the native admin so that OIDC finds have something to return.")
call, resp = pystep("a6-probe-before-enable", "token")
add("a6a", "Acquire an Entra access token for the DocumentDB scope (claims subset only, token never recorded)", call, resp,
    "AzureCliCredential returned a v1.0 token for aud https://ossrdbms-aad.database.windows.net with idp live.com (a personal Microsoft account), scp user_impersonation, issued by the signed-in tenant with oid equal to the signed-in user's object id.")
call, resp = pystep("a6-probe-before-enable", "OIDC_CALLBACK:ping")
c2, r2 = pystep("a6-probe-before-enable", "construct:OIDC_CALLBACK")
add("a6b", "MONGODB-OIDC ping before Entra is enabled (PyMongo 4.20.2, Learn-shaped OIDCCallback, plain host)",
    [c2, call], {"construct": r2, "ping": resp, "callback_calls": py("a6-probe-before-enable")["callback_calls"]},
    "With NativeAuth only, the service rejects a token-bearing MONGODB-OIDC saslStart with code 18 AuthenticationFailed \"The authentication mechanism provided is not supported in the service.\" and no errorLabels; the open-source gateway also answers code 18 AuthenticationFailed but with \"'MONGODB-OIDC' is not a supported authentication scheme.\", so the code is the same and the message differs.",
    "different", OS_PARITY + " step 00f2: code 18 AuthenticationFailed \"'MONGODB-OIDC' is not a supported authentication scheme.\" (empty payload)")

# ---------------------------------------------------------------- (b) enable
r = recs["b0-update-help"]
add("b0", "Check whether the CLI has a flag for authConfig (Learn's CLI pivot uses --auth-allowed-modes)", r["command"],
    {"exit_code": r["exit_code"], "excerpt_verbatim": help_excerpt(r, "AuthConfig Arguments", "Compute Arguments")},
    "The documentdb extension 1.0.0 exposes --auth-allowed-modes with allowed values NativeAuth and MicrosoftEntraID, so the CLI method from Learn was used instead of az rest PATCH.")
r = recs["b1-update-auth-allowed-modes"]
add("b1", "Enable MicrosoftEntraID alongside NativeAuth (Learn method)", r["command"], azresp(r),
    "The update exited 0 after 155.4 s with no stderr; its returned resource already listed allowedModes [MicrosoftEntraID, NativeAuth] but still showed provisioningState and clusterStatus 'Updating'.")
r = recs["b2-poll-1"]
add("b2", "Read state right after the update returned", r["command"], azresp(r),
    "The first show, 0.6 s after the update returned, reported provisioningState Succeeded, clusterStatus Ready and allowedModes [\"MicrosoftEntraID\", \"NativeAuth\"] (the service reorders the list).")
r = recs["b3-time-to-apply"]
add("b3", "Time to apply", r["command"], {"update_command_wall_s": r["update_command_wall_s"], "polls": r["polls"]},
    "Enabling Entra took 155.4 s end to end through the CLI's long-running-operation wait, and nothing further was pending when it returned.")
r = recs["b4-native-ping-after-enable"]
add("b4", "Native SCRAM ping after enabling Entra", [c["call"] + "   # client: " + c["client"] for c in r["calls"]], r["calls"],
    "Native authentication kept working after Entra was added (ping ok: 1).")
r = recs["b5-hello-saslSupportedMechs-after-enable"]
add("b5", "hello saslSupportedMechs after enabling Entra", [c["call"] for c in r["calls"]], r["calls"],
    "After enabling Entra, hello advertises saslSupportedMechs ['MONGODB-OIDC', 'SCRAM-SHA-256'] for every user string, including one that is not registered, whereas the open-source gateway only ever advertises SCRAM-SHA-256.",
    "different", OS_PARITY + " steps 00d-00f")
call, resp = pystep("b6-probe-after-enable-before-assign", "OIDC_CALLBACK:ping")
call = [pystep("b6-probe-after-enable-before-assign", "construct:OIDC_CALLBACK")[0], call]
add("b6", "MONGODB-OIDC ping after enabling Entra but before registering the identity (PyMongo 4.20.2)", call,
    {"ping": resp, "callback_calls": py("b6-probe-after-enable-before-assign")["callback_calls"]},
    "Once Entra is enabled the token is evaluated, and an unregistered principal gets code 18 AuthenticationFailed \"External identity is not present in the system.\" with no errorLabels; the open-source gateway cannot reach this stage because it rejects the mechanism.",
    "different", OS_PARITY + " step 00f2")

# ---------------------------------------------------------------- (c) CLI help
r = recs["c1-mongocluster-help"]
add("c1", "Find the Entra user command group", r["command"], {"exit_code": r["exit_code"], "stdout": r["stdout"]},
    "az documentdb mongocluster lists four subgroups (firewall-rule, identity, microsoft-entra-user, replica); microsoft-entra-user is the one for Entra users.")
r = recs["c2-entra-user-help"]
add("c2", "microsoft-entra-user group help", r["command"], {"exit_code": r["exit_code"], "stdout": r["stdout"]},
    "The group has assign, list, remove, show and wait.")
r = recs["c3-entra-user-assign-help"]
add("c3", "assign --help: accepted --type values (verbatim)", r["command"],
    {"exit_code": r["exit_code"], "type_parameter_verbatim": help_excerpt(r, "    --type -t", "Resource Id Arguments").rstrip(),
     "object_id_parameter_verbatim": help_excerpt(r, "    --name --object-id -n", "    --resource-group").rstrip(),
     "full_stdout": r["stdout"]},
    "The --type (-t) parameter accepts exactly User and ServicePrincipal (help: \"Allowed values: User, ServicePrincipal. Example: --type User.  Allowed values: ServicePrincipal, User.\"), and --object-id is still described as \"Object ID (client ID)\", matching DECISIONS topic 5.")
for sub in ("list", "show", "remove"):
    r = recs[f"c4-entra-user-{sub}-help"]
    add(f"c4-{sub}", f"microsoft-entra-user {sub} --help", r["command"], {"exit_code": r["exit_code"], "stdout": r["stdout"]},
        f"The {sub} subcommand help was recorded for completeness; it takes --cluster-name and --resource-group" + (" and --object-id." if sub != "list" else "."))
for sg in ("firewall-rule", "identity", "replica"):
    r = recs[f"c6-subgroup-{sg}-help"]
    add(f"c6-{sg}", f"{sg} subgroup help", r["command"], {"exit_code": r["exit_code"], "stdout": r["stdout"]},
        "This subgroup does not manage Entra users" + (" (identity manages the cluster's own managed identities)." if sg == "identity" else "."))

# ---------------------------------------------------------------- (d) identity and assignment
r = recs["d1-signed-in-user-id"]
add("d1", "Signed-in identity object id (masked)", r["command"], {"exit_code": r["exit_code"], "stdout": r["stdout"], "stderr": r["stderr"]},
    "az ad signed-in-user show returned an object id (a GUID, masked here), so the Graph lookup works for this account.")
r = recs["d1b-signed-in-user-type"]
add("d1b", "Characterise the account type without recording personal fields", r["command"], azresp(r),
    "The account is a personal Microsoft account federated into its own directory as userType Member (UPN carries the #EXT# marker, identity issuer MicrosoftAccount), not a B2B guest.")
r = recs["d2-entra-user-assign"]
add("d2", "Assign the signed-in identity as an administrative Entra identity (Learn CLI example)", r["command"],
    dict(azresp(r), wall_s=recs["d2b-assign-wall"]["wall_s"]),
    "The assignment succeeded in 63.6 s: users/<object-id> was created with identityProvider MicrosoftEntraID, principalType 'User' and roles [{db: admin, role: root}], so a personal Microsoft account is accepted as an Entra administrator.")
r = recs["d3-entra-user-list"]
add("d3", "List registered principals", r["command"], azresp(r),
    "The list returns the native administrator (no identityProvider) and the new Entra administrator.")
r = recs["d4-entra-user-show"]
add("d4", "Show the registered principal", r["command"], azresp(r),
    "show returns the same users resource: principalType User, role root on admin, provisioningState Succeeded.")
r = recs["d5-arm-users-list"]
add("d5", "ARM REST view of the users child resources (api-version 2026-06-01)", r["command"], azresp(r),
    "The REST response carries two fields the CLI drops, properties.user and identityProvider.properties.entraTenant (the tenant id, masked), and the native admin appears as users/factoryadmin.")
call, resp = pystep("d6-probe-after-assign-1", "OIDC_CALLBACK:ping")
call2, resp2 = pystep("d6-probe-after-assign-1", "OIDC_CALLBACK:find")
add("d6", "First MONGODB-OIDC attempt after the assignment (8 s after assign returned; PyMongo 4.20.2)", [pystep("d6-probe-after-assign-1", "construct:OIDC_CALLBACK")[0], call, call2],
    {"started_at": py("d6-probe-after-assign-1")["started_at"], "ping": resp, "find": resp2},
    "The very first attempt, 8 s after the assign command returned, authenticated and ran ping and find, so there was no observable replication delay.")
r = recs["d7-native-admin-usersinfo"]
add("d7", "How the native admin sees the Entra administrator", [c["call"] for c in r["calls"]], r["calls"],
    "The native admin sees the Entra administrator as user '<object-id>' in db 'admin' with role root and customData.IdentityProvider {type: MicrosoftEntraID, properties: {principalType: 'user'}} (lower-case, unlike ARM's 'User').")

# ---------------------------------------------------------------- (e) PyMongo versions
pip_resp = {}
for lab, v in (("e1-pymongo-4.6.3", "4.6.3"), ("e2-pymongo-4.7.0", "4.7.0"), ("e3-pymongo-latest", "latest")):
    d = py(lab)
    pip_resp[v] = {"python": d["python"], "pymongo": d["pymongo"], "azure_identity": d["azure_identity"],
                   "pip_log": open(os.path.join(RAW, f"pip-{v}.log")).read().strip()}
add("e0", "Create throwaway venvs and install each PyMongo with azure-identity",
    ["/opt/homebrew/bin/python3.13 -m venv venvs/pm-4.6.3 venvs/pm-4.7.0 venvs/pm-latest (one call per venv)",
     "venvs/pm-4.6.3/bin/python -m pip install --disable-pip-version-check -q 'pymongo==4.6.3' azure-identity",
     "venvs/pm-4.7.0/bin/python -m pip install --disable-pip-version-check -q 'pymongo==4.7.0' azure-identity",
     "venvs/pm-latest/bin/python -m pip install --disable-pip-version-check -q pymongo azure-identity"],
    {"exit_codes": [0, 0, 0], "resolved": pip_resp, "also_resolved_in_each": "azure-core 1.41.0, msal 1.39.0, dnspython 2.9.2"},
    "All three installs succeeded on Python 3.13.13; 'latest' resolved to PyMongo 4.20.2 and every venv got azure-identity 1.27.0.")
# 4.6.3
for nm, title, reading in (
        ("import_oidc_callback_api", "PyMongo 4.6.3: import Learn's callback API",
         "PyMongo 4.6.3 has no OIDCCallback class, so Learn's Python sample fails at import with ImportError before any network traffic."),
        ("construct:OIDC_CALLBACK", "PyMongo 4.6.3: OIDC_CALLBACK with a Learn-shaped callback object",
         "Passing a callback object under OIDC_CALLBACK is rejected at MongoClient construction with ValueError \"Auth mechanism property values must be strings or callback functions\"."),
        ("request_token_callback_default_hosts:ping", "PyMongo 4.6.3 pre-GA API: request_token_callback, default allowed_hosts",
         "The undocumented pre-GA request_token_callback is refused client-side with ConfigurationError because the resolved host fc-a472369cc681-000.mongocluster.cosmos.azure.com is not in the default authOIDCAllowedHosts list."),
        ("request_token_callback_allowed_hosts:ping", "PyMongo 4.6.3 pre-GA API: request_token_callback with allowed_hosts ['*.mongocluster.cosmos.azure.com']",
         "With the Azure host allowed, PyMongo 4.6.3 fails inside its own authenticate() with KeyError 'MONGODB-OIDC' (the mechanism is missing from _AUTH_MAP), so 4.6.3 cannot authenticate with MONGODB-OIDC at all and the callback is never called.")):
    call, resp = pystep("e1-pymongo-4.6.3", nm)
    if nm.endswith(":ping"):
        c0, r0 = pystep("e1-pymongo-4.6.3", "construct:" + nm.split(":")[0])
        call, resp = [c0, call], {"construct": r0, "ping": resp,
                                  "find": pystep("e1-pymongo-4.6.3", nm.split(":")[0] + ":find")[1]}
    add("e1-" + nm.replace(":", "-"), title, call, resp, reading, "not_tested_locally")
# 4.7.0 as Learn writes it
c0, r0 = pystep("e2-pymongo-4.7.0", "construct:OIDC_CALLBACK")
c1, r1 = pystep("e2-pymongo-4.7.0", "OIDC_CALLBACK:ping")
c2, r2 = pystep("e2-pymongo-4.7.0", "OIDC_CALLBACK:find")
add("e2", "PyMongo 4.7.0: Learn's Python callback as written (no ALLOWED_HOSTS), plain host", [c0, c1, c2],
    {"construct": r0, "ping": r1, "find": r2, "callback_calls": py("e2-pymongo-4.7.0")["callback_calls"],
     "other_calls": "insert, connectionStatus and usersInfo failed with the same ConfigurationError (raw/oidc_py_e2-pymongo-4.7.0.json)"},
    "PyMongo 4.7.0 refuses to authenticate to the Azure host with ConfigurationError \"Refusing to connect to fc-a472369cc681-000.mongocluster.cosmos.azure.com, which is not in authOIDCAllowedHosts: [...]\" before calling the callback, so Learn's Python sample does not work on 4.7.0 as written.",
    "not_tested_locally")
lab = "e2b-pymongo-4.7.0-allowed-azure"
c0, r0 = pystep(lab, "construct:OIDC_CALLBACK")
add("e2b", "PyMongo 4.7.0 with ALLOWED_HOSTS ['*.azure.com']: ping, find, insert", [c0] + [pystep(lab, n)[0] for n in ("OIDC_CALLBACK:ping", "OIDC_CALLBACK:find", "OIDC_CALLBACK:insert_one", "OIDC_CALLBACK:find_after_insert")],
    {"construct": r0, **{n.split(":")[1]: pystep(lab, n)[1] for n in ("OIDC_CALLBACK:ping", "OIDC_CALLBACK:find", "OIDC_CALLBACK:insert_one", "OIDC_CALLBACK:find_after_insert")},
     "callback_calls": py(lab)["callback_calls"]},
    "Adding ALLOWED_HOSTS ['*.azure.com'] to the same 4.7.0 client makes it authenticate (one callback call) and ping, find and insert all succeed.",
    "not_tested_locally")
lab = "e2c-pymongo-4.7.0-allowed-mongocluster"
c0, r0 = pystep(lab, "construct:OIDC_CALLBACK")
add("e2c", "PyMongo 4.7.0 with ALLOWED_HOSTS ['*.mongocluster.cosmos.azure.com']: ping, find", [c0, pystep(lab, "OIDC_CALLBACK:ping")[0], pystep(lab, "OIDC_CALLBACK:find")[0]],
    {"construct": r0, "ping": pystep(lab, "OIDC_CALLBACK:ping")[1], "find": pystep(lab, "OIDC_CALLBACK:find")[1]},
    "The narrower pattern '*.mongocluster.cosmos.azure.com' works on 4.7.0 too.", "not_tested_locally")
lab = "e3-pymongo-latest"
c0, r0 = pystep(lab, "construct:OIDC_CALLBACK")
add("e3", "PyMongo 4.20.2 (latest): Learn's callback as written, plain host: ping, find, insert",
    [c0] + [pystep(lab, n)[0] for n in ("OIDC_CALLBACK:ping", "OIDC_CALLBACK:find", "OIDC_CALLBACK:insert_one", "OIDC_CALLBACK:find_after_insert")],
    {"construct": r0, **{n.split(":")[1]: pystep(lab, n)[1] for n in ("OIDC_CALLBACK:ping", "OIDC_CALLBACK:find", "OIDC_CALLBACK:insert_one", "OIDC_CALLBACK:find_after_insert")},
     "callback_calls": py(lab)["callback_calls"]},
    "PyMongo 4.20.2 connects with Learn's callback and no ALLOWED_HOSTS, calls the callback once (context timeout_seconds 60, version 1, username '', no idp_info) and runs ping, find and insert.",
    "not_tested_locally")
for nm, reading in (
        ("connectionStatus_showPrivileges", "connectionStatus with showPrivileges reports the Entra identity as user '<object-id>' in db 'admin' with role root and three privilege entries (any db/collection, cluster, and admin db)."),
        ("connectionStatus", "Plain connectionStatus returns authenticatedUsers and authenticatedUserRoles only."),
        ("usersInfo_oid_admin", "usersInfo '<object-id>' on admin returns the identity's user document with roles [root@admin] and customData.IdentityProvider {type: MicrosoftEntraID, properties: {principalType: 'user'}}."),
        ("usersInfo_userdoc_admin", "usersInfo {user: '<object-id>', db: 'admin'} returns the same document."),
        ("usersInfo_userdoc_external", "usersInfo {user: '<object-id>', db: '$external'} is rejected with code 2 BadValue \"Unsupported value specified for 'db' field. Only 'admin' is allowed.\", so Entra users live in admin, not $external."),
        ("usersInfo_external_db", "Running usersInfo '<object-id>' against the $external database succeeds and still returns the user in db 'admin'."),
        ("usersInfo_oid_showPrivileges", "usersInfo with showPrivileges for the identity returns inheritedPrivileges for the root role."),
        ("usersInfo_1", "usersInfo: 1 lists both administrators (the Entra identity and factoryadmin)."),
        ("usersInfo_forAllDBs", "usersInfo {forAllDBs: true} returns the same two users."),
        ("listDatabases_nameOnly", "listDatabases works for the Entra administrator (only mt_entra existed at that moment).")):
    call, resp = pystep(lab, "OIDC_CALLBACK:" + nm)
    add("e3-" + nm, "PyMongo 4.20.2 as the Entra identity: " + nm, call, resp, reading,
        "not_tested_locally")
lab = "e3b-pymongo-latest-global-host"
add("e3b", "PyMongo 4.20.2 against the .global. host", [pystep(lab, "construct:OIDC_CALLBACK")[0], pystep(lab, "OIDC_CALLBACK:ping")[0], pystep(lab, "OIDC_CALLBACK:find")[0]],
    {"ping": pystep(lab, "OIDC_CALLBACK:ping")[1], "find": pystep(lab, "OIDC_CALLBACK:find")[1]},
    "The global read-write host form works with MONGODB-OIDC too.", "not_tested_locally")
# 4.7.0 vs 4.11 boundary
bisect = {"4.7.0": "if not properties.environment:", "4.7.1": "if not properties.environment:", "4.7.2": "if not properties.environment:",
          "4.7.3": "if not properties.environment:", "4.8.0": "if not properties.environment:", "4.9.0": "if not properties.environment:",
          "4.9.1": "if not properties.environment:", "4.9.2": "if not properties.environment:", "4.10.0": "if not properties.environment:",
          "4.10.1": "if not properties.environment:", "4.11": "if properties.human_callback is not None:",
          "4.11.3": "if properties.human_callback is not None:", "4.12.0": "if properties.human_callback is not None:",
          "4.13.0": "if properties.human_callback is not None:"}
add("e4", "Extra: which PyMongo release stopped enforcing ALLOWED_HOSTS for machine callbacks (source of each release)",
    ["/opt/homebrew/bin/python3.13 -m venv venvs/pm-bisect; venvs/pm-bisect/bin/python -m pip install -q azure-identity dnspython",
     "for v in 4.7.0 4.7.1 4.7.2 4.7.3 4.8.0 4.9.0 4.9.1 4.9.2 4.10.0 4.10.1 4.11 4.11.3 4.12.0 4.13.0: pip install -q --no-deps --force-reinstall pymongo==$v; grep -rh -A1 'Validate that the address is allowed' <site-packages>/pymongo --include='*.py'"],
    {"line_after_'# Validate that the address is allowed'": bisect,
     "4.20.2 (pm-latest venv)": "auth_oidc_shared.py line 208: if properties.human_callback is not None:",
     "pymongo_changelog": "the 4.7.x-4.11 changelog entries do not mention the change (learn/pymongo-changelog.rst)"},
    "From 4.7.0 through 4.10.1 PyMongo checks ALLOWED_HOSTS for every MONGODB-OIDC credential without ENVIRONMENT, including a custom OIDC_CALLBACK, and from 4.11 only for human callbacks.",
    "not_tested_locally")
for v in ("4.10.1", "4.11"):
    lab = f"e5-bisect-pymongo-{v}"
    add(f"e5-{v}", f"Extra: live check of PyMongo {v} with Learn's callback and no ALLOWED_HOSTS",
        [pystep(lab, "construct:OIDC_CALLBACK")[0], pystep(lab, "OIDC_CALLBACK:ping")[0]],
        {"pymongo": py(lab)["pymongo"], "ping": pystep(lab, "OIDC_CALLBACK:ping")[1], "find": pystep(lab, "OIDC_CALLBACK:find")[1],
         "callback_calls": len(py(lab)["callback_calls"])},
        ("PyMongo 4.10.1 still refuses the Azure host with the same ConfigurationError." if v == "4.10.1" else
         "PyMongo 4.11 connects without ALLOWED_HOSTS, so 4.11 is the first release on which Learn's Python sample works as written."),
        "not_tested_locally")

# ---------------------------------------------------------------- (f) Node
add("f0", "Install mongodb@6.6.0, mongodb@6.7.0 (and latest as an extra) with the latest @azure/identity in a temp directory",
    "cd <test-dir>/node && npm install --ignore-scripts --no-audit --no-fund mongodb660@npm:mongodb@6.6.0 mongodb670@npm:mongodb@6.7.0 mongodblatest@npm:mongodb@latest @azure/identity@latest",
    {"exit_code": 0, "npm_log": open(os.path.join(RAW, "npm-install.log")).read().strip(),
     "resolved": {"mongodb660": "6.6.0", "mongodb670": "6.7.0", "mongodblatest": "7.9.1", "@azure/identity": node["azure_identity"]},
     "node": node["node"], "npm": "11.19.0"},
    "npm installed 65 packages; latest resolved to mongodb 7.9.1 and @azure/identity 4.14.1 on Node v24.21.0.")
node_readings = {
    "6.6.0-oidc_callback-allowed-azure.com": ("Node driver 6.6.0 does not know OIDC_CALLBACK: the client constructor throws MongoInvalidArgumentError \"Either a PROVIDER_NAME or a REQUEST_TOKEN_CALLBACK must be specified for mechanism 'MONGODB-OIDC'.\"", "f1"),
    "6.6.0-oidc_callback-allowed-mongocluster": ("The same constructor error occurs with ALLOWED_HOSTS ['*.mongocluster.cosmos.azure.com'], so 6.6.0 cannot run Learn's TypeScript sample with either pattern.", "f2"),
    "6.6.0-oidc_callback-no-allowed-hosts": ("Without ALLOWED_HOSTS 6.6.0 fails the same way at construction.", "f3"),
    "6.6.0-legacy-request_token_callback-allowed-mongocluster": ("Extra: 6.6.0's pre-GA REQUEST_TOKEN_CALLBACK sends a token-less saslStart first and the service answers code 18 AuthenticationFailed \"JWT token missing from OIDC payload\" (errorLabels HandshakeError and ResetPool are added by the driver; the server reply has none), so the pre-GA two-step flow does not work either.", "f4"),
    "6.7.0-oidc_callback-allowed-azure.com": ("Node driver 6.7.0 with Learn's OIDC_CALLBACK and ALLOWED_HOSTS ['*.azure.com'] connects, pings and finds; the callback is called once with params {timeoutContext, version: 1}.", "f5"),
    "6.7.0-oidc_callback-allowed-mongocluster": ("6.7.0 with ALLOWED_HOSTS ['*.mongocluster.cosmos.azure.com'] also connects, pings and finds.", "f6"),
    "6.7.0-oidc_callback-no-allowed-hosts": ("Control: without ALLOWED_HOSTS 6.7.0 refuses client-side with MongoInvalidArgumentError \"Host 'fc-a472369cc681-000.mongocluster.cosmos.azure.com:10260' is not valid for OIDC authentication with ALLOWED_HOSTS of '*.mongodb.net,...'\" and never calls the callback.", "f7"),
    "6.7.0-learn-ts-expiry-allowed-azure.com": ("Extra: Learn's TypeScript expiry formula yields expiresInSeconds 1793854691680 and 6.7.0 still connects, so the documented bug has no runtime effect here.", "f8"),
    "latest-oidc_callback-allowed-azure.com": ("Node driver 7.9.1 with ALLOWED_HOSTS ['*.azure.com'] connects, pings and finds.", "f9"),
    "latest-oidc_callback-allowed-mongocluster": ("7.9.1 with ALLOWED_HOSTS ['*.mongocluster.cosmos.azure.com'] connects, pings and finds.", "f10"),
    "latest-oidc_callback-no-allowed-hosts": ("Control: 7.9.1 without ALLOWED_HOSTS fails the same way as 6.7.0 (MongoInvalidArgumentError for host 'fc-a472369cc681-000.mongocluster.cosmos.azure.com:10260'), its default list now ending in '*.mongo.com' and still containing no Azure domain.", "f11"),
    "latest-learn-ts-expiry-allowed-azure.com": ("Extra: 7.9.1 also ignores the wrong expiresInSeconds and connects.", "f12"),
    "latest-oidc_callback-allowed-mongocluster-global-host": ("Extra: against the .global. host, '*.mongocluster.cosmos.azure.com' still matches (the check runs on the SRV-resolved host) and 7.9.1 connects.", "f13"),
}
for lab, (reading, sid) in node_readings.items():
    call, resp = nodestep(lab)
    add(sid, f"Node {lab}", call, resp, reading, "not_tested_locally")

# ---------------------------------------------------------------- (g) like-for-like with the open-source parity test
r = recs["g1-raw-saslStart-MONGODB-OIDC"]
add("g1", "Raw unauthenticated MONGODB-OIDC saslStart without a token (same command as open-source parity step 00f2)",
    [c["call"] for c in r["calls"]], r["calls"],
    "With Entra enabled, a saslStart without a JWT (empty or principal-only payload) gets code 18 AuthenticationFailed \"JWT token missing from OIDC payload\" with no errorLabels, so the service supports only the one-step JWT flow, whereas the open-source gateway answers the identical command with \"'MONGODB-OIDC' is not a supported authentication scheme.\"",
    "different", OS_PARITY + " step 00f2")

# ---------------------------------------------------------------- after and cleanup
r = recs["z1-authConfig-after"]
add("z1", "properties.authConfig after the test (left enabled)", r["command"], azresp(r),
    "Entra stays enabled alongside native auth: allowedModes [\"MicrosoftEntraID\", \"NativeAuth\"].")
r = recs["z2-show-after"]
add("z2", "Full cluster resource after the test (masked)", r["command"], azresp(r),
    "Apart from authConfig and lastModifiedAt (22:28:32Z) the resource is unchanged; properties.connectionString is still the SCRAM-SHA-256 string.")
r = recs["z3-connection-strings-after"]
add("z3", "Connection strings after enabling Entra", r["command"], azresp(r),
    "Enabling Entra adds two MONGODB-OIDC strings without credentials, GlobalMicrosoftEntraId and MicrosoftEntraId, next to the two SCRAM strings.")
r = recs["y1-drop-database"]
add("y1", "Drop the test database", [c["call"] for c in r["calls"]], r["calls"],
    "mt_entra was dropped and a filtered listDatabases confirms it is gone.")
r = recs["y2-delete-venvs-node_modules"]
add("y2", "Delete the throwaway venvs and node_modules", r["command"], {"removed": r["removed"], "still_present": r["still_present"]},
    "All four venvs (4.6.3, 4.7.0, latest, bisect) and node/node_modules were deleted; package.json and package-lock.json are kept as a record.")

report = {
    "test": "m-entra",
    "goal": "Microsoft Entra ID on the managed service: enable it, register the signed-in identity as administrator, and find which PyMongo and Node driver versions can authenticate with MONGODB-OIDC.",
    "database": "mt_entra (seeded over native auth, used by the OIDC finds and inserts, dropped at the end)",
    "observed_on": "2026-11-25",
    "run_window_utc": {"started": min(r["recorded_at"] for r in recs.values()), "finished": max(r["recorded_at"] for r in recs.values()),
                       "note": "g1 (raw saslStart, no database access) ran after the cleanup steps y1/y2"},
    "cluster": {
        "resource": "Microsoft.DocumentDB/mongoClusters ddb-samples-shared, resource group documentdb-samples-rg, eastus",
        "shape": "M30, shardCount 1, serverVersion 8.0, PremiumSSDv2 128 GB, HA Disabled, public network access",
        "engine_identity": {"hello.maxWireVersion": 25, "hello.internal.documentdb_versions": ["2.2-1", "2.3.0", "12.1-1"], "hello.internal.kind": "azuredocumentdb"},
    },
    "signed_in_identity": {
        "object_id": "<object-id-masked>",
        "kind": "personal Microsoft account (token idp live.com) that is a Member of its own directory; UPN has the #EXT# marker; identities: federated/MicrosoftAccount and userPrincipalName",
        "token": "v1.0, aud https://ossrdbms-aad.database.windows.net, scp user_impersonation, appid Azure CLI",
    },
    "client": {
        "az": "azure-cli 2.89.1, extension documentdb 1.0.0",
        "python": "3.13.13 (Homebrew) in throwaway venvs",
        "pymongo_tested": ["4.6.3", "4.7.0", "4.10.1 (extra)", "4.11 (extra)", "4.20.2 (latest)"],
        "azure_identity_python": "1.27.0",
        "native_helper": "project venv pymongo 4.20.1",
        "node": node["node"], "npm": "11.19.0",
        "node_mongodb_tested": ["6.6.0", "6.7.0", "7.9.1 (latest, extra)"],
        "azure_identity_node": node["azure_identity"],
    },
    "sources_read_first": [
        "findings/phase4/DECISIONS.md: 'Driver and ODM version floors (SME topic 4)' items 4.1, 4.2, 4.12-open; 'Microsoft Entra ID specifics (SME topic 5)' (all items)",
        "findings/phase4/ENGINE-TESTS.md: 'Local gateway parity (topic 12)' and 'Driver floors (topic 4)'; engine-tests-1.2/local-gateway-parity/report.json steps 00d-00f2",
        "https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (ms.date 2026-03-11, updated_at 2026-11-23; saved as learn/rbac.html and learn/rbac.txt)",
    ],
    "steps": steps,
    "config_changes": [
        "properties.authConfig.allowedModes changed from [\"NativeAuth\"] to [\"MicrosoftEntraID\", \"NativeAuth\"] with `az documentdb mongocluster update --name ddb-samples-shared --resource-group documentdb-samples-rg --auth-allowed-modes NativeAuth MicrosoftEntraID` (started 2026-11-25T22:28:32Z, 155.4 s); left enabled as instructed.",
        "Added the administrative Entra user resource Microsoft.DocumentDB/mongoClusters/ddb-samples-shared/users/<object-id-masked> (identityProvider MicrosoftEntraID, principalType User, roles [{db: admin, role: root}]) for the signed-in account with `az documentdb mongocluster microsoft-entra-user assign --object-id <object-id-masked> --cluster-name ddb-samples-shared --resource-group documentdb-samples-rg --type User --role db=admin role=root` (created 2026-11-25T22:32:10Z, 63.6 s); not removed.",
    ],
    "not_config_changes": "Database mt_entra was created and dropped; no other database was touched. The throwaway venvs and node_modules were deleted.",
    "scripts": {
        "common": os.path.join(TEST_DIR, "common.py"),
        "az_steps": os.path.join(TEST_DIR, "az_steps.py"),
        "native_helper": os.path.join(TEST_DIR, "native.py"),
        "python_oidc_probe": os.path.join(TEST_DIR, "oidc_py.py"),
        "node_oidc_probe": os.path.join(TEST_DIR, "oidc_node.mjs"),
        "node_runner": os.path.join(TEST_DIR, "run_node.py"),
        "raw_saslStart": os.path.join(TEST_DIR, "raw_sasl.py"),
        "report_builder": os.path.join(TEST_DIR, "build_report.py"),
        "conclusions": os.path.join(TEST_DIR, "conclusions.json"),
        "raw": [os.path.join(RAW, "steps.jsonl"), os.path.join(RAW, "oidc_node.json")] + sorted(
            os.path.join(RAW, f) for f in os.listdir(RAW) if f.startswith("oidc_py_")),
    },
    "masking": "Password, URIs with credentials, subscription id, tenant id, tenant domain, object ids, e-mail addresses and the account name are masked; access tokens were never recorded (only a claims subset).",
}
report["conclusions"] = json.load(open(os.path.join(TEST_DIR, "conclusions.json")))
report = common.mask(report)
SESSION_FIX = ("-Users-julietai-claude/<guid-masked>/scratchpad", "-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad")
text = json.dumps(report, indent=1).replace(*SESSION_FIX)
with open(os.path.join(TEST_DIR, "report.json"), "w") as fh:
    fh.write(text)
print(len(steps), "steps;", os.path.getsize(os.path.join(TEST_DIR, "report.json")), "bytes")
