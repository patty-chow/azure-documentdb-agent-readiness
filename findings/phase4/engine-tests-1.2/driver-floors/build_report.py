"""Assemble report.json for driver-floors (engine 1.2.0 rerun) from out/*.json written by run.py.
Run: /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I build_report.py
No database access; readings are computed from the recorded responses."""
import json
import os
import re

WORK = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/driver-floors"
OUT = os.path.join(WORK, "out")
OLD_REPORT = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/driver-floors/report.json"
PINS = ["4.8.0", "4.9", "4.11", "4.13"]
DB = "t_drivers"


def load(name):
    with open(os.path.join(OUT, name)) as fh:
        return json.load(fh)


def J(x):
    return json.dumps(x, default=str, separators=(", ", ": "))


def short(p):
    return p.replace(WORK + "/", "")


def cmdline(rec):
    return short(rec["command"])


def proc_resp(rec, keep_stdout=True):
    s = f"exit={rec['exit']}" + (" (TIMED OUT)" if rec.get("timed_out") else "")
    if keep_stdout and rec.get("stdout", "").strip():
        s += "; stdout: " + rec["stdout"].strip()
    if rec.get("stderr", "").strip():
        s += "; stderr: " + rec["stderr"].strip()
    return short(s)


def show_fields(rec):
    keep = [l for l in rec.get("stdout", "").splitlines() if re.match(r"^(Name|Version|Requires|Required-by):", l)]
    s = f"exit={rec['exit']}; " + " | ".join(keep) if keep else f"exit={rec['exit']}"
    if rec.get("stderr", "").strip():
        s += "; stderr: " + rec["stderr"].strip()
    return s


def res(r):
    """ok/response/error of one recorded driver call as a compact string."""
    if r is None:
        return "not recorded"
    if r.get("ok") is True:
        return J(r.get("response"))
    if r.get("ok") is None:
        return str(r.get("response"))
    return "ERROR " + J(r.get("error"))


def wire(probe, phase, names=None, events=("started", "succeeded", "failed")):
    out = []
    for e in probe.get("wire", []):
        if e["phase"] != phase or e["event"] not in events:
            continue
        if names and e["command_name"] not in names:
            continue
        body = e.get("command") if e["event"] == "started" else (e.get("reply") if e["event"] == "succeeded" else e.get("failure"))
        out.append(f"{e['event']} {e['command_name']} {J(body)}")
    return out


steps = []


def step(name, command, response, reading):
    steps.append({"step": name, "command": command, "response": response, "reading": reading})


# ---------------------------------------------------------------- env
env = load("env.json")
hello = env["hello"]["response"] if env["hello"]["ok"] else {}
bi = env["buildInfo"]["response"] if env["buildInfo"]["ok"] else {}
dv = (hello.get("internal") or {}).get("documentdb_versions")
di = env["docker_inspect"]["stdout"].strip().split("|", 5)
image, image_id, status, health, started_at, labels_json = (di + [""] * 6)[:6]
labels = json.loads(labels_json) if labels_json.startswith("{") else {}
dimg = env.get("docker_image_inspect", {})
_dg = dimg.get("stdout", "").strip().split("|")[0] if dimg else ""
try:
    digests = ", ".join(json.loads(_dg))
except Exception:
    digests = _dg
py3 = env["python3_version"]["stdout"].strip()

step("Interpreter used for every throwaway venv",
     "python3 --version; shutil.which('python3'); os.path.realpath(that path)",
     f"{proc_resp(env['python3_version'])}; which={env['python3_which']['which']}; realpath={env['python3_which']['realpath']}",
     f"Every venv below was made with `python3 -m venv` from Homebrew {py3}, not from the repo .venv.")
step("Container identity",
     cmdline(env["docker_inspect"]),
     proc_resp(env["docker_inspect"]),
     f"Container ddb-engine-test is {status}/{health} on image {image}, whose OCI labels give version "
     f"{labels.get('org.opencontainers.image.version')} and revision {labels.get('org.opencontainers.image.revision')} "
     f"(built {labels.get('org.opencontainers.image.created')}).")
if dimg:
    step("Image digest",
         cmdline(dimg),
         proc_resp(dimg),
         f"The image digest is {digests}, the reference to pin when reproducing this run.")
step("buildInfo (repo .venv driver, pymongo " + env["orchestrator_pymongo"] + ")",
     "MongoClient(LOCAL_URI, serverSelectionTimeoutMS=15000).admin.command('buildInfo')",
     res(env["buildInfo"]),
     f"buildInfo reports version {bi.get('version')} (the MongoDB version the gateway advertises) and has no field naming the engine release.")
step("hello (repo .venv driver)",
     "MongoClient(LOCAL_URI, serverSelectionTimeoutMS=15000).admin.command('hello')",
     res(env["hello"]),
     f"The gateway advertises wire versions {hello.get('minWireVersion')}-{hello.get('maxWireVersion')}, msg '{hello.get('msg')}' and "
     f"internal.documentdb_versions {dv}, so the engine under test is 1.2.0 even though buildInfo says {bi.get('version')}.")
step(f"{DB} pre-state",
     env["pre_listDatabases"]["command"],
     res(env["pre_listDatabases"]),
     f"{DB} {'existed' if env['pre_t_drivers_present'] else 'did not exist'} when the final run started"
     + (" (collections left by this session's earlier iterations of these same scripts), so it was dropped first." if env["pre_t_drivers_present"] else ", so nothing had to be dropped."))
if env["pre_t_drivers_present"]:
    step(f"{DB} leftover collections", env["pre_collections"]["command"], res(env["pre_collections"]),
         "Only this test's own probe collections were present.")
    step(f"Drop leftover {DB} before the run", env["pre_drop"]["command"], res(env["pre_drop"]),
         f"The engine dropped {DB}, so every collection seen later was created by this final run.")
    step(f"{DB} after the pre-run drop", env["pre_listDatabases_after_drop"]["command"], res(env["pre_listDatabases_after_drop"]),
         f"{DB} was absent at the start of the final run.")

# ---------------------------------------------------------------- pymongo
wc = load("wheelcheck.json")
macos = (wc.get("macos_product_version") or {}).get("stdout", "?").strip()
matrix = {}
for pin in PINS:
    r = load(f"pymongo-{pin}.json")
    pj = r.get("probe_json") or {}
    R = pj.get("results", {})
    ver = pj.get("pymongo.__version__", "?")
    inst_lines = [l.strip() for l in r["pip_install"]["stdout"].splitlines() if l.strip()]
    wheel = next((l for l in inst_lines if "pymongo-" in l and l.endswith(".whl")), "")
    local_built = "macosx_27_0" in wheel
    step(f"pymongo=={pin}: create venv, install, freeze",
         f"1) {cmdline(r['venv_create'])}  2) {cmdline(r['pip_install'])}  3) {cmdline(r['pip_freeze'])}",
         f"1) exit={r['venv_create']['exit']}  2) exit={r['pip_install']['exit']}; " + " / ".join(inst_lines)
         + f"  3) exit={r['pip_freeze']['exit']}; " + ", ".join(r["pip_freeze"]["stdout"].split()),
         f"pip installed pymongo {ver} with dnspython {pj.get('dist_versions', {}).get('dnspython')} "
         + (f"from a cp313 wheel in pip's local cache; PyPI publishes no cp313 file for 4.8.0 (next step), so that wheel was built locally from the official "
            f"sdist by an earlier install (its macosx_27_0 tag matches this Mac's macOS {macos})." if local_built
            else "from PyPI's cp313 macOS arm64 wheel (served from pip's cache)."))
    if pin == "4.8.0":
        step("PyPI files for pymongo 4.8.0 (explains the 4.8.0 install line)",
             wc["command"] + " ; sw_vers -productVersion", J(wc.get("response") or wc.get("error")) + f" ; sw_vers: {macos}",
             "PyPI has no cp313 wheel for 4.8.0 (macOS arm64 wheels stop at cp312), so on Python 3.13 pip builds it from the sdist; "
             "the driver code is the same release either way.")
    imp = R.get("import_AsyncMongoClient", {})
    step(f"pymongo {ver}: import AsyncMongoClient",
         imp.get("command", "from pymongo import AsyncMongoClient"),
         (imp.get("response") if imp.get("ok") else "ERROR " + J(imp.get("error"))) + f"; python warnings: {J(pj.get('warnings'))}",
         (f"pymongo {ver} ships AsyncMongoClient (pymongo.asynchronous.mongo_client) and raises no warning on import."
          if imp.get("ok") else
          f"pymongo {ver} has no AsyncMongoClient at all, so the async API is unavailable with this pin (a driver fact, independent of the engine)."))
    pa, pd = R.get("async_ping_admin"), R.get("async_ping_db")
    if imp.get("ok"):
        both = bool(pa and pa.get("ok") and pd and pd.get("ok"))
        step(f"pymongo {ver}: async ping",
             f"{pa.get('command')}; {pd.get('command')}",
             f"admin: {res(pa)}; {DB}: {res(pd)}",
             (f"AsyncMongoClient from pymongo {ver} authenticated over TLS with SCRAM-SHA-256 and got ok 1.0 from the 1.2.0 engine on admin and {DB}."
              if both else f"The async ping with pymongo {ver} failed against the 1.2.0 engine; the exact error is in the response."))
        si = R.get("async_server_info")
        step(f"pymongo {ver}: async server_info()",
             si.get("command"), res(si),
             (f"Through the async client the server reports version {si['response'].get('version')}, the same as buildInfo from the sync driver."
              if si and si.get("ok") else "server_info() failed through the async client."))
        crud = R.get("extra_async_crud", {})
        all_ok = bool(crud) and all(v.get("ok") for v in crud.values())
        step(f"pymongo {ver}: EXTRA (beyond the spec) async insert_one / find_one / delete_one / count_documents",
             " ; ".join(v.get("command", k) for k, v in crud.items()),
             " ; ".join(f"{k}: {res(v)}" for k, v in crud.items()),
             (f"Past ping, a full async write/read/delete round trip on {DB}.{pj.get('coll')} worked with pymongo {ver} (deleted_count 1, count 0 afterwards)."
              if all_ok else f"The extra async CRUD round trip with pymongo {ver} did not fully succeed; see the response."))
    else:
        step(f"pymongo {ver}: async ping",
             pa.get("command") if pa else "await AsyncMongoClient(LOCAL_URI).admin.command('ping')",
             res(pa),
             f"No async ping is possible with pymongo {ver} because the import fails; this is the expected result below the floor.")
    sc = R.get("sync_ping_control", {})
    step(f"pymongo {ver}: sync MongoClient ping (control)",
         sc.get("command"), res(sc),
         ((f"The sync client of the same pin also gets ok 1.0, so connection and credentials are good and any async difference would be the async API itself."
           if imp.get("ok") else
           f"pymongo {ver}'s sync MongoClient works against the 1.2.0 engine (ok 1.0); only the async API is missing from this release.")
          if sc.get("ok") else "The sync control ping failed, so the async result for this pin cannot be attributed to the async API."))
    matrix[pin] = {
        "installed": ver, "has_c": pj.get("pymongo.has_c()"), "wheel_line": wheel, "async_import_ok": imp.get("ok"),
        "async_import_error": None if imp.get("ok") else (imp.get("error") or {}).get("str"),
        "async_ping_admin": None if not imp.get("ok") else (pa or {}).get("response"),
        "async_ping_db": None if not imp.get("ok") else (pd or {}).get("response"),
        "async_server_info_version": ((R.get("async_server_info") or {}).get("response") or {}).get("version"),
        "extra_async_crud_ok": (all(v.get("ok") for v in R.get("extra_async_crud", {}).values()) if R.get("extra_async_crud") else None),
        "sync_ping_ok": sc.get("ok"), "warnings": pj.get("warnings"),
    }

# ---------------------------------------------------------------- beanie
beanie_summary = {}
for nm, spec in (("beanie2", "beanie>=2,<3"), ("beanie1", "beanie<2")):
    r = load(f"{nm}.json")
    pj = r.get("probe_json") or {}
    R = pj.get("results", {})
    v = pj.get("dist_versions", {})
    lbl = f"{nm} ({spec})"
    inst_lines = [l.strip() for l in r["pip_install"]["stdout"].splitlines() if l.strip()]
    motor_lines = [l for l in inst_lines if "motor" in l.lower()]
    freeze = r["pip_freeze"]["stdout"].split()
    pulls_motor = any(x.lower().startswith("motor==") for x in freeze)
    step(f"{lbl}: create venv, install, freeze",
         f"1) {cmdline(r['venv_create'])}  2) {cmdline(r['pip_install'])}  3) {cmdline(r['pip_freeze'])}",
         f"1) exit={r['venv_create']['exit']}  2) exit={r['pip_install']['exit']}; " + " / ".join(inst_lines)
         + f"  3) exit={r['pip_freeze']['exit']}; " + ", ".join(freeze),
         (f"pip resolved beanie {v.get('beanie')} and pulled motor {v.get('motor')} ({motor_lines[0] if motor_lines else ''}), with pymongo {v.get('pymongo')} arriving through motor."
          if pulls_motor else
          f"pip resolved beanie {v.get('beanie')} with pymongo {v.get('pymongo')} and pydantic {v.get('pydantic')}; motor appears nowhere in the resolution or the freeze."))
    step(f"{lbl}: pip show beanie / motor / pymongo",
         f"1) {cmdline(r['pip_show_beanie'])}  2) {cmdline(r['pip_show_motor'])}  3) {cmdline(r['pip_show_pymongo'])}",
         f"1) {show_fields(r['pip_show_beanie'])}  2) {show_fields(r['pip_show_motor'])}  3) {show_fields(r['pip_show_pymongo'])}"
         + ("  (motor's License field, the full Apache-2.0 text, omitted here; it is in out/beanie1.json)" if pulls_motor else ""),
         ("beanie lists motor under Requires, motor is Required-by beanie, and pymongo is Required-by motor, so the driver reaches Beanie 1 only through Motor."
          if pulls_motor else
          "beanie lists pymongo directly under Requires and `pip show motor` finds no such package."))
    im = R.get("import_motor", {})
    step(f"{lbl}: declared runtime requirements and `import motor`",
         "importlib.metadata.requires('beanie') (entries without an extra marker); import motor",
         f"requires: {J(pj.get('beanie_requires_runtime'))}; import motor: " + (im.get("response") if im.get("ok") else "ERROR " + J(im.get("error"))),
         ("Beanie's own metadata requires motor>=2.5.0,<4.0.0 and motor imports, so Motor is a hard runtime dependency of Beanie 1."
          if im.get("ok") else
          "Beanie's own metadata requires pymongo>=4.11.0,!=4.15.0,<5.0.0 and no motor, and `import motor` fails."))
    ib = R.get("import_beanie", {})
    step(f"{lbl}: import beanie",
         ib.get("command"), ib.get("response") if ib.get("ok") else "ERROR " + J(ib.get("error")),
         f"beanie {v.get('beanie')} imports on Python {pj.get('python')}; the client used next is {pj.get('client_class')}.")
    ini = R.get("init_beanie", {})
    w_init = wire(pj, "init_beanie", events=("succeeded", "failed"))
    step(f"{lbl}: init_beanie",
         ini.get("command"),
         res(ini) + " ; wire replies during init: " + " | ".join(w_init),
         (f"init_beanie on {pj.get('client_class')} completed on the 1.2.0 engine: listIndexes on the not-yet-existing collection returned code 26 NamespaceNotFound "
          f"(PyMongo's list_indexes turns that into an empty index list) and createIndexes then created the collection and name_1."
          if ini.get("ok") else "init_beanie failed on the 1.2.0 engine; the exact error is in the response."))
    ix = R.get("index_information_after_init", {})
    step(f"{lbl}: index_information after init",
         ix.get("command"), res(ix),
         "The engine lists _id_ and name_1, and adds storageEngine {enableOrderedIndex: true} to name_1, an option Beanie did not send in createIndexes.")
    ins = R.get("insert", {})
    step(f"{lbl}: insert", ins.get("command"), res(ins) + " ; wire: " + " | ".join(wire(pj, "insert")),
         "The insert was acknowledged (n 1) and Beanie set the document id." if ins.get("ok") else "The insert failed; see the response.")
    f1, f2, g = R.get("find_one", {}), R.get("find_to_list", {}), R.get("get_by_id", {})
    find_ok = all(x.get("ok") for x in (f1, f2, g))
    step(f"{lbl}: find (find_one on the indexed field, find().to_list(), get by id)",
         f"{f1.get('command')} ; {f2.get('command')} ; {g.get('command')}",
         f"find_one: {res(f1)} ; find().to_list(): {res(f2)} ; get: {res(g)}",
         "All three reads returned the inserted document (same id, name 'hello', n 1)." if find_ok else "At least one read failed; see the response.")
    dl, cn = R.get("delete", {}), R.get("count_after_delete", {})
    step(f"{lbl}: delete and count",
         f"{dl.get('command')} ; {cn.get('command')}",
         f"delete: {res(dl)} ; count: {res(cn)} ; wire: " + " | ".join(wire(pj, "delete", names={"delete"}) + wire(pj, "count_after_delete")),
         ("The delete removed the document (deleted_count 1) and Beanie's count, an aggregate with $group that returns an empty batch, gives 0."
          if dl.get("ok") and cn.get("ok") and cn.get("response") == 0 else "The delete or the count did not behave as expected; see the response."))
    ra = R.get("init_beanie_again_new_client", {})
    step(f"{lbl}: EXTRA (beyond the spec) second init_beanie from a new client on the existing collection (an app restart)",
         ra.get("command"),
         res(ra) + " ; wire: " + " | ".join(wire(pj, "init_beanie_again_new_client", names={"listIndexes", "createIndexes"}, events=("started", "succeeded", "failed"))[:4]),
         ("On restart Beanie sends createIndexes for name_1 again (it does so on every init) and the engine answers ok with note 'all indexes already exist', "
          "so the engine-added storageEngine option does not make the repeat createIndexes conflict."
          if ra.get("ok") else "A second init_beanie failed on the existing collection; see the response."))
    rd = R.get("init_beanie_allow_index_dropping_new_client", {})
    w_drop = wire(pj, "init_beanie_allow_index_dropping_new_client", names={"dropIndexes", "createIndexes"}, events=("started", "succeeded", "failed"))
    dropped = any(x.startswith("succeeded dropIndexes") for x in w_drop)
    step(f"{lbl}: EXTRA (beyond the spec) init_beanie(..., allow_index_dropping=True) from a new client on the unchanged model",
         rd.get("command"),
         res(rd) + " ; wire: " + " | ".join(w_drop),
         ("With allow_index_dropping=True Beanie dropped name_1 (nIndexesWas 2) and rebuilt it although the model did not change, because Beanie compares every "
          "index option except key and v (read from beanie/odm/fields.py) and the engine's storageEngine option makes the listed index look different."
          if dropped else "With allow_index_dropping=True Beanie did not drop the unchanged index."))
    ws = pj.get("warnings", [])
    step(f"{lbl}: Python warnings during import and all steps",
         "warnings.catch_warnings(record=True) + simplefilter('always') around the whole probe",
         J(ws),
         ("No warning was raised." if not ws else
          f"{len(ws)} warnings, all {', '.join(sorted({w['category'] for w in ws}))} from {', '.join(sorted({w['where'] for w in ws}))}; none came from Motor."))
    beanie_summary[nm] = {
        "spec": spec, "versions": v, "freeze": freeze, "pulls_motor": pulls_motor, "motor_resolution_lines": motor_lines,
        "beanie_requires_runtime": pj.get("beanie_requires_runtime"), "client_class": pj.get("client_class"),
        "steps_ok": {k: x.get("ok") for k, x in R.items()},
        "index_after_init": (ix.get("response") or {}).get("name_1"),
        "allow_index_dropping_drops_unchanged_index": dropped, "warnings": ws,
    }

# ---------------------------------------------------------------- cleanup
c = load("cleanup.json")
step("Delete the throwaway venvs",
     f"1) {cmdline(c['du_venvs'])}  2) {cmdline(c['ls_venvs'])}  3) {cmdline(c['rm_venvs'])}  4) {c['venvs_exists_after_rm']['command']}",
     f"1) {proc_resp(c['du_venvs'])}  2) {', '.join(c['ls_venvs']['stdout'].split())}  3) exit={c['rm_venvs']['exit']}  4) {c['venvs_exists_after_rm']['response']}",
     f"All six venvs ({c['du_venvs']['stdout'].split()[0] if c['du_venvs'].get('stdout') else '?'}) were deleted and the venvs directory no longer exists.")
step(f"{DB} contents before the final drop",
     f"{c['pre_drop_listDatabases']['command']} ; {c['pre_drop_collections']['command']}",
     f"{res(c['pre_drop_listDatabases'])} ; {res(c['pre_drop_collections'])}",
     f"{DB} held only the five collections this run created, all empty because every probe deleted what it inserted.")
step(f"Drop {DB}", c["drop"]["command"], res(c["drop"]),
     f"The engine confirmed the drop of {DB}." if c["drop"].get("ok") else "The drop failed; see the response.")
step(f"{DB} after the drop", c["post_drop_listDatabases"]["command"], res(c["post_drop_listDatabases"]),
     f"{DB} no longer exists; apart from admin-level ping, buildInfo, hello and this filtered listDatabases, no other database was touched." if not c["post_drop_listDatabases"]["response"].get("databases") else f"{DB} still exists.")

# ---------------------------------------------------------------- comparison with the 0.117 run
comparison = {"previous_report": OLD_REPORT}
try:
    old = json.load(open(OLD_REPORT))
    om = old["summary"]["pymongo_matrix"]
    rows = {}
    for pin, okey in zip(PINS, ["4.8.0", "4.9.0", "4.11.0", "4.13.0"]):
        o, n = om.get(okey, {}), matrix[pin]
        rows[pin] = {"installed_0.117": o.get("installed"), "installed_1.2.0": n["installed"],
                     "async_import_ok_0.117": o.get("async_import_ok"), "async_import_ok_1.2.0": n["async_import_ok"],
                     "async_ping_ok_0.117": o.get("async_ping_ok"),
                     "async_ping_ok_1.2.0": (None if not n["async_import_ok"] else (n["async_ping_admin"] == {"ok": 1.0} and n["async_ping_db"] == {"ok": 1.0})),
                     "sync_ping_ok_0.117": o.get("sync_ping_ok"), "sync_ping_ok_1.2.0": n["sync_ping_ok"]}
    comparison["pymongo"] = rows
    ob = old["summary"]["beanie"]
    comparison["beanie"] = {
        nm: {"0.117": {"beanie": ob[nm]["beanie"], "pymongo": ob[nm]["pymongo"], "motor": ob[nm]["motor"], "roundtrip_ok": ob[nm]["roundtrip"]["ok"],
                       "roundtrip_recorded": list(ob[nm]["roundtrip"]["response"].keys())},
             "1.2.0": {"beanie": beanie_summary[nm]["versions"]["beanie"], "pymongo": beanie_summary[nm]["versions"]["pymongo"],
                       "motor": beanie_summary[nm]["versions"]["motor"], "roundtrip_ok": all(beanie_summary[nm]["steps_ok"].get(k) for k in
                       ("init_beanie", "insert", "find_one", "find_to_list", "get_by_id", "delete", "count_after_delete"))}}
        for nm in ("beanie2", "beanie1")}
    same = all(r["async_import_ok_0.117"] == r["async_import_ok_1.2.0"] and r["async_ping_ok_0.117"] == r["async_ping_ok_1.2.0"]
               and r["sync_ping_ok_0.117"] == r["sync_ping_ok_1.2.0"] and str(r["installed_0.117"]) == str(r["installed_1.2.0"]) for r in rows.values()) and all(
        b["0.117"]["beanie"] == b["1.2.0"]["beanie"] and b["0.117"]["motor"] == b["1.2.0"]["motor"] and b["0.117"]["roundtrip_ok"] == b["1.2.0"]["roundtrip_ok"]
        for b in comparison["beanie"].values())
    comparison["same_outcomes"] = same
    comparison["note"] = ("The 0.117 run (image tag latest = 0.117.0 at the time, same database name) recorded only insert/find_one/count for Beanie 2 and "
                          "insert/count for Beanie 1; this run adds get, delete, count after delete, restart re-init, allow_index_dropping re-init, "
                          "wire capture and an async CRUD round trip per pymongo pin.")
except Exception as e:
    comparison["error"] = repr(e)

b2, b1 = beanie_summary["beanie2"], beanie_summary["beanie1"]
conclusions = [
    {"question": "4.5: Which PyMongo pins can use AsyncMongoClient against engine 1.2.0?",
     "answer": (f"pymongo 4.8.0 cannot: `from pymongo import AsyncMongoClient` raises ImportError (cannot import name 'AsyncMongoClient' from 'pymongo'). "
                f"pymongo 4.9, 4.11 and 4.13.0 import it (pymongo.asynchronous.mongo_client.AsyncMongoClient, no import warning) and each got ping "
                f"{{'ok': 1.0}} on admin and {DB}, server_info version 7.0.0, and a working async insert/find/delete. The sync ping control passed for all four pins. "
                f"On this engine the import is the only floor among these pins: 4.9 is the first release with the API and 4.13 the GA release (beta/GA status per DECISIONS 4.5); the engine adds no further floor."),
     "confidence": "observed"},
    {"question": "4.6: Does Beanie 2 (pip install \"beanie>=2,<3\") complete init/insert/find/delete on AsyncMongoClient against engine 1.2.0?",
     "answer": (f"Yes. pip resolved beanie {b2['versions']['beanie']} + pymongo {b2['versions']['pymongo']} + pydantic {b2['versions']['pydantic']} with no motor. "
                f"Its metadata requires pymongo>=4.11.0,!=4.15.0,<5.0.0. init_beanie on AsyncMongoClient (listIndexes returned code 26 NamespaceNotFound on the new collection, which PyMongo treats as no indexes, "
                f"then createIndexes created it), insert, find_one, find().to_list(), get, delete (deleted_count 1) and count (0) all succeeded with no Python warnings."),
     "confidence": "observed"},
    {"question": "4.6: Does pip install \"beanie<2\" pull Motor?",
     "answer": (f"Yes. It resolves beanie {b1['versions']['beanie']}, whose runtime requirement motor>=2.5.0,<4.0.0 pulls motor {b1['versions']['motor']} "
                f"('Collecting motor<4.0.0,>=2.5.0 (from beanie<2)'). Motor in turn pulls pymongo {b1['versions']['pymongo']} ('pymongo<5.0,>=4.9 (from motor...)'). "
                f"pip show reports beanie Requires motor, motor Required-by beanie, and pymongo Required-by motor."),
     "confidence": "observed"},
    {"question": "Does Beanie 1 + Motor (as resolved today) still work against engine 1.2.0?",
     "answer": (f"Yes. The same round trip through motor.motor_asyncio.AsyncIOMotorClient succeeded (beanie {b1['versions']['beanie']}, motor {b1['versions']['motor']}, "
                f"pymongo {b1['versions']['pymongo']}). The only difference from Beanie 2 was {len(b1['warnings'])} PydanticDeprecatedSince211 warnings from "
                f"lazy_model/parser/new.py:107 (lazy-model 0.2.0, which Beanie 1 pins exactly). Motor raised no warning."),
     "confidence": "observed"},
    {"question": "Were the Beanie 1/Motor failures seen in earlier sample runs ('MotorDatabase object is not callable'; cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor') caused by the engine?",
     "answer": ("Probably not. A fresh unpinned beanie<2 resolution works against the engine, and those errors are client-library mismatches. "
                "Those samples' exact pins were not re-run here, so this stays inferred."),
     "confidence": "inferred"},
    {"question": "EXTRA: Is it safe to call init_beanie again on every app restart against engine 1.2.0?",
     "answer": ("With the default allow_index_dropping=False, yes. Beanie re-sends createIndexes for name_1 on every init, and the engine answers ok with "
                "note 'all indexes already exist', so there is no conflict even though listIndexes adds storageEngine {enableOrderedIndex: true}. "
                "With allow_index_dropping=True, no. Both Beanie 2.2.0 and 1.30.0 sent dropIndexes name_1 (reply nIndexesWas 2) and then createIndexes name_1 "
                "(numIndexesBefore 1, numIndexesAfter 2) for an unchanged model. So every restart with that flag drops and rebuilds each Beanie-declared secondary index."),
     "confidence": "observed"},
    {"question": "EXTRA: Why does allow_index_dropping=True rebuild unchanged indexes on this engine, and would MongoDB do the same?",
     "answer": ("In the installed Beanie source (beanie/odm/fields.py, IndexModelField), index equality compares every option except 'key' and 'v'. "
                "The engine adds storageEngine {enableOrderedIndex: true} to the secondary indexes it lists: name_1 here, and the TTL and partial-unique "
                "indexes in the 0.117 ttl-semantics and partial-unique reports. So the listed index never equals the declared one. A server that lists only the options Beanie sent would "
                "compare equal and drop nothing. That half was not tested here (no MongoDB server). A kit or Learn note should say: do not run Beanie with "
                "allow_index_dropping=True against DocumentDB, or expect an index rebuild per start."),
     "confidence": "inferred"},
    {"question": "Did any engine-dependent result change between engine 0.117 (first run) and 1.2.0?",
     "answer": ("No. The same versions resolved and every pin and both Beanie lines had the same outcome." if comparison.get("same_outcomes") else
                "Yes, see comparison_with_engine_0.117 in the report.") + " This run also checked more than the 0.117 run did (see comparison note).",
     "confidence": "observed"},
    {"question": "What does buildInfo report, and which engine version do these facts describe?",
     "answer": (f"buildInfo: {J(bi)}, the MongoDB version the gateway advertises (wire {hello.get('minWireVersion')}-{hello.get('maxWireVersion')}). "
                f"The engine version comes from hello.internal.documentdb_versions {dv} and the image label org.opencontainers.image.version="
                f"{labels.get('org.opencontainers.image.version')} (image {image}, revision {labels.get('org.opencontainers.image.revision')}, digest {digests})."),
     "confidence": "observed"},
    {"question": "Do these results prove managed Azure DocumentDB behaviour?",
     "answer": ("No. They are observations of the open-source engine 1.2.0 and its gateway in documentdb-local: one node, SCRAM-SHA-256 only, TLS with a "
                "self-signed certificate, and retryWrites=false in the URI. The managed service may run a different engine or gateway build. The AsyncMongoClient, "
                "Beanie and storageEngine/allow_index_dropping results need a managed-cluster check before Learn or the kit quotes them as service behaviour."),
     "confidence": "inferred"},
    {"question": "4.11-open: what floors does this evidence support stating in kit text?",
     "answer": ("Maintainer decision. The evidence supports gating AsyncMongoClient on pymongo>=4.13 (GA); 4.9 and 4.11 import and work here but predate GA (4.10 and 4.12 were not tested). "
                "It also supports stating that Beanie 2 needs pymongo>=4.11,!=4.15.0 and no Motor, and that `pip install \"beanie<2\"` silently installs Motor "
                "(3.7.1 today), which topic 4.7 records as past end of life on May 14, 2026. The allow_index_dropping caveat above is a new item for the Beanie guidance."),
     "confidence": "inferred"},
]

report = {
    "test": "driver-floors",
    "variant": "ENGINE 1.2.0 RERUN of the engine-dependent part only; the changelog (OIDC) and npm-history parts were skipped as already settled",
    "database": DB,
    "run_window_utc": {"started": env.get("started"), "finished": c.get("finished")},
    "decisions_md_topic": "findings/phase4/DECISIONS.md, 'Driver and ODM version floors (SME topic 4)': 4.5 (AsyncMongoClient floor 4.9/4.11/4.13), "
                          "4.6 (Beanie 2 on AsyncMongoClient vs Beanie 1 + Motor), 4.11-open (whether kit skills state floors)",
    "engine": {
        "container": "ddb-engine-test", "image": image, "image_id": image_id, "repo_digests": digests, "status": f"{status}/{health}",
        "started_at": started_at, "oci_labels": labels, "buildInfo": bi,
        "hello": {k: hello.get(k) for k in ("isWritablePrimary", "msg", "minWireVersion", "maxWireVersion", "maxBsonObjectSize",
                                            "maxMessageSizeBytes", "maxWriteBatchSize", "logicalSessionTimeoutMinutes", "readOnly",
                                            "saslSupportedMechs", "internal", "ok")},
        "engine_version_statement": f"buildInfo reports {bi.get('version')} (MongoDB-compatible version, wire {hello.get('maxWireVersion')}); the engine is 1.2.0 per "
                                    f"hello.internal.documentdb_versions {dv} and OCI label version {labels.get('org.opencontainers.image.version')}.",
        "evidence_scope": "Everything here is evidence about the open-source DocumentDB engine 1.2.0 and its gateway as packaged in documentdb-local "
                          "(buildInfo 7.0.0, wire 21); it does not prove managed Azure DocumentDB behaviour.",
    },
    "connection": {"uri_masked": env["uri_masked"],
                   "note": "credentials are test values for the throwaway container, read from local.env and never written here"},
    "interpreter": {"python3": py3, "which": env["python3_which"]["which"], "realpath": env["python3_which"]["realpath"],
                    "venv_pip": (load("pymongo-4.9.json").get("pip_version") or {}).get("stdout", "").split(" from ")[0]},
    "steps": steps,
    "summary": {"pymongo_matrix": matrix, "beanie": beanie_summary},
    "comparison_with_engine_0.117": comparison,
    "conclusions": conclusions,
    "cleanup": {"venvs_deleted": c["venvs_exists_after_rm"]["response"] is False, "venvs_size_before_delete": c["du_venvs"].get("stdout", "").split("\t")[0],
                "database_dropped": c["drop"].get("response"), "database_absent_after": not c["post_drop_listDatabases"]["response"].get("databases")},
    "scripts": {"orchestrator": os.path.join(WORK, "run.py"), "pymongo_probe": os.path.join(WORK, "probe_pymongo.py"),
                "beanie_probe": os.path.join(WORK, "probe_beanie.py"), "report_builder": os.path.join(WORK, "build_report.py"),
                "rerun": "cd out && /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I ../run.py all && "
                         "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I ../build_report.py"},
    "raw_outputs": sorted(os.path.join(OUT, f) for f in os.listdir(OUT) if f.endswith(".json")),
    "notes": [
        "Pins were installed exactly as specified (pymongo==4.8.0, ==4.9, ==4.11, ==4.13); ==4.9 / ==4.11 / ==4.13 resolve to the first release of each line (4.9, 4.11, 4.13.0), which is what a floor test needs.",
        "pip served every file from its local cache; the 4.8.0 cp313 wheel in that cache was built locally from the official sdist because PyPI publishes no cp313 wheel for 4.8.0.",
        "Steps marked EXTRA go beyond the spec: an async CRUD round trip per pymongo pin, Beanie get/count, a restart re-init, an allow_index_dropping re-init, and wire capture through pymongo command monitoring (allowlisted data and index commands only; authentication commands are never recorded).",
        "The scripts were iterated during this session: warning capture was added to probe_pymongo.py, and the re-inits and wire capture to probe_beanie.py. Every output in out/ and this report comes from one clean end-to-end `run.py all` of the final scripts. Its env phase dropped the t_drivers left by those iterations before anything else ran.",
        "The LOCAL_URI password never appears in any script, output or this report; run.py scrubs the URI and password from every captured stdout and stderr.",
    ],
}
with open(os.path.join(WORK, "report.json"), "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print(f"wrote {os.path.join(WORK, 'report.json')} with {len(steps)} steps and {len(conclusions)} conclusions; same_outcomes_vs_0.117={comparison.get('same_outcomes')}")
