"""driver-floors: ENGINE 1.2.0 RERUN of the engine-dependent part only (no changelog / npm history parts).

Run with the repo venv (it has pymongo) in isolated mode, one phase per call:
  /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -I run.py <phase>
Phases, in order:
  env      interpreter used for the venvs, container identity (docker inspect), buildInfo + hello,
           t_drivers pre-state (dropped first if a previous attempt left it behind)
  pymongo  one throwaway venv per pin (python3 -m venv): pymongo==4.8.0, ==4.9, ==4.11, ==4.13 (`run.py pymongo <pin>` for one),
           then probe_pymongo.py inside each: AsyncMongoClient import + async ping (+ extra async CRUD, sync control)
  beanie2  throwaway venv, pip install "beanie>=2,<3", probe_beanie.py round trip on AsyncMongoClient
  beanie1  throwaway venv, pip install "beanie<2": does it pull motor? then the same round trip via Motor
  wheelcheck  PyPI file list for pymongo 4.8.0 (explains the cached locally built cp313 wheel in its install log)
  cleanup  delete every venv, drop t_drivers, verify both
  all      the six phases above in order
Then build the report: <repo venv python> -I build_report.py
Every external command is capped at 280 s (the limit per command is 5 minutes).
LOCAL_URI is parsed from local.env and passed only to the probe processes; it is never printed, and every
captured stdout/stderr is scrubbed of the URI and the password before it is written to out/."""
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.parse

WORK = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests-1.2/driver-floors"
ENVF = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"
OUT = os.path.join(WORK, "out")
VENVS = os.path.join(WORK, "venvs")
DB = "t_drivers"
CONTAINER = "ddb-engine-test"
TIMEOUT = 280
PYMONGO_PINS = ["4.8.0", "4.9", "4.11", "4.13"]


def load_env(path):
    env = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            env[k] = v
    return env


E = load_env(ENVF)
URI = E["LOCAL_URI"]
_pw = E.get("LOCAL_PASS", "")
SECRETS = sorted({s for s in (URI, _pw, urllib.parse.quote(_pw, safe="")) if s}, key=len, reverse=True)
URI_MASKED = re.sub(r"(mongodb(?:\+srv)?://[^:/@]+:)[^@]*@", r"\1***@", URI)


def scrub(x):
    s = x if isinstance(x, str) else str(x)
    for sec in SECRETS:
        s = s.replace(sec, "***")
    return s


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def run(argv, env_extra=None, cwd=OUT, timeout=TIMEOUT):
    env = dict(os.environ)
    env.update({"PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INPUT": "1"})
    env.pop("LOCAL_URI", None)
    if env_extra:
        env.update(env_extra)
    t0 = time.monotonic()
    rec = {"command": shlex.join(argv), "cwd": cwd, "started": now()}
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        rec.update(exit=p.returncode, timed_out=False, stdout=scrub(p.stdout), stderr=scrub(p.stderr))
    except subprocess.TimeoutExpired as e:
        so = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        se = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        rec.update(exit=None, timed_out=True, stdout=scrub(so), stderr=scrub(se))
    rec["elapsed_s"] = round(time.monotonic() - t0, 2)
    return rec


def err(e):
    d = {"type": f"{type(e).__module__}.{type(e).__name__}", "str": scrub(e)}
    det = getattr(e, "details", None)
    if isinstance(det, dict):
        for k in ("ok", "code", "codeName", "errmsg", "errorLabels"):
            if k in det:
                d[k] = det[k]
    return d


def attempt(command, fn):
    t0 = time.monotonic()
    try:
        r = {"ok": True, "command": command, "response": fn()}
    except Exception as e:
        r = {"ok": False, "command": command, "error": err(e)}
    r["elapsed_s"] = round(time.monotonic() - t0, 3)
    return r


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w") as fh:
        fh.write(scrub(json.dumps(obj, indent=2, default=str)))
    print(f"wrote {path}")


def client():
    from pymongo import MongoClient
    return MongoClient(URI, serverSelectionTimeoutMS=15000)


def list_db(c):
    return attempt(f"client.admin.command('listDatabases', nameOnly=True, filter={{'name': '{DB}'}})",
                   lambda: c.admin.command("listDatabases", nameOnly=True, filter={"name": DB}))


def phase_env():
    import pymongo
    r = {"phase": "env", "started": now(), "uri_masked": URI_MASKED, "orchestrator_python": sys.version.split()[0],
         "orchestrator_pymongo": pymongo.__version__}
    r["python3_version"] = run(["python3", "--version"])
    w = shutil.which("python3")
    r["python3_which"] = {"command": "shutil.which('python3'); os.path.realpath(...)", "which": w,
                          "realpath": os.path.realpath(w) if w else None}
    fmt = "{{.Config.Image}}|{{.Image}}|{{.State.Status}}|{{.State.Health.Status}}|{{.State.StartedAt}}|{{json .Config.Labels}}"
    r["docker_inspect"] = run(["docker", "inspect", CONTAINER, "--format", fmt])
    image = r["docker_inspect"]["stdout"].split("|", 1)[0].strip() if r["docker_inspect"]["exit"] == 0 else None
    if image:
        r["docker_image_inspect"] = run(["docker", "image", "inspect", image, "--format", "{{json .RepoDigests}}|{{.Created}}"])
    c = client()
    try:
        r["buildInfo"] = attempt("client.admin.command('buildInfo')", lambda: c.admin.command("buildInfo"))
        r["hello"] = attempt("client.admin.command('hello')", lambda: c.admin.command("hello"))
        r["pre_listDatabases"] = list_db(c)
        present = bool(r["pre_listDatabases"].get("ok")) and any(
            d.get("name") == DB for d in r["pre_listDatabases"]["response"].get("databases", []))
        r["pre_t_drivers_present"] = present
        if present:
            r["pre_collections"] = attempt(f"client['{DB}'].list_collection_names()", lambda: c[DB].list_collection_names())
            r["pre_drop"] = attempt(f"client['{DB}'].command('dropDatabase')", lambda: c[DB].command("dropDatabase"))
            r["pre_listDatabases_after_drop"] = list_db(c)
    finally:
        c.close()
    r["finished"] = now()
    save("env.json", r)


def mkvenv(name):
    v = os.path.join(VENVS, name)
    shutil.rmtree(v, ignore_errors=True)
    os.makedirs(VENVS, exist_ok=True)
    rec = {"venv": v, "venv_create": run(["python3", "-m", "venv", v])}
    py = os.path.join(v, "bin", "python")
    rec["venv_python_version"] = run([py, "-I", "--version"])
    rec["pip_version"] = run([py, "-I", "-m", "pip", "--version"])
    return v, py, rec


def phase_pymongo(pins=None):
    for pin in (pins or PYMONGO_PINS):
        name = f"pymongo-{pin}"
        v, py, rec = mkvenv(name)
        rec.update(phase="pymongo", pin=pin, started=now())
        rec["pip_install"] = run([py, "-I", "-m", "pip", "install", f"pymongo=={pin}"])
        rec["pip_freeze"] = run([py, "-I", "-m", "pip", "freeze"])
        coll = "async_probe_" + pin.replace(".", "_")
        rec["probe"] = run([py, "-I", os.path.join(WORK, "probe_pymongo.py"), "--db", DB, "--coll", coll],
                           env_extra={"LOCAL_URI": URI})
        try:
            rec["probe_json"] = json.loads(rec["probe"]["stdout"])
        except Exception as e:
            rec["probe_json_error"] = repr(e)
        rec["finished"] = now()
        save(f"{name}.json", rec)


def beanie_phase(name, spec, coll):
    v, py, rec = mkvenv(name)
    rec.update(phase=name, spec=spec, started=now())
    rec["pip_install"] = run([py, "-I", "-m", "pip", "install", spec])
    rec["pip_freeze"] = run([py, "-I", "-m", "pip", "freeze"])
    rec["pip_show_beanie"] = run([py, "-I", "-m", "pip", "show", "beanie"])
    rec["pip_show_motor"] = run([py, "-I", "-m", "pip", "show", "motor"])
    rec["pip_show_pymongo"] = run([py, "-I", "-m", "pip", "show", "pymongo"])
    rec["probe"] = run([py, "-I", os.path.join(WORK, "probe_beanie.py"), "--db", DB, "--coll", coll],
                       env_extra={"LOCAL_URI": URI})
    try:
        rec["probe_json"] = json.loads(rec["probe"]["stdout"])
    except Exception as e:
        rec["probe_json_error"] = repr(e)
    rec["finished"] = now()
    save(f"{name}.json", rec)


def phase_cleanup():
    r = {"phase": "cleanup", "started": now()}
    r["du_venvs"] = run(["du", "-sh", VENVS]) if os.path.isdir(VENVS) else {"command": f"du -sh {VENVS}", "note": "venvs dir absent"}
    r["ls_venvs"] = run(["ls", "-1", VENVS]) if os.path.isdir(VENVS) else None
    r["rm_venvs"] = run(["rm", "-rf", VENVS])
    r["venvs_exists_after_rm"] = {"command": f"os.path.exists('{VENVS}')", "response": os.path.exists(VENVS)}
    c = client()
    try:
        r["pre_drop_listDatabases"] = list_db(c)

        def colls():
            return {n: c[DB][n].count_documents({}) for n in sorted(c[DB].list_collection_names())}

        r["pre_drop_collections"] = attempt(f"{{n: client['{DB}'][n].count_documents({{}}) for n in client['{DB}'].list_collection_names()}}", colls)
        r["drop"] = attempt(f"client['{DB}'].command('dropDatabase')", lambda: c[DB].command("dropDatabase"))
        r["post_drop_listDatabases"] = list_db(c)
    finally:
        c.close()
    r["finished"] = now()
    save("cleanup.json", r)


def phase_wheelcheck():
    """Supporting fact for the 4.8.0 install log: which files PyPI publishes for pymongo 4.8.0 (no engine involved)."""
    import urllib.request
    url = "https://pypi.org/pypi/pymongo/4.8.0/json"
    r = {"phase": "wheelcheck", "started": now(), "command": f"GET {url}  -> [u['filename'] for u in urls]"}
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            d = json.load(resp)
        files = [u["filename"] for u in d.get("urls", [])]
        r["response"] = {"file_count": len(files),
                         "cp313_files": [f for f in files if "cp313" in f],
                         "macosx_arm64_files": [f for f in files if "macosx" in f and "arm64" in f],
                         "sdists": [f for f in files if f.endswith(".tar.gz")],
                         "requires_python": d.get("info", {}).get("requires_python")}
        r["ok"] = True
    except Exception as e:
        r["ok"] = False
        r["error"] = repr(e)
    r["macos_product_version"] = run(["sw_vers", "-productVersion"])  # to read the platform tag of a locally built wheel
    r["finished"] = now()
    save("wheelcheck.json", r)


PHASES = {
    "env": phase_env,
    "pymongo": phase_pymongo,
    "beanie2": lambda: beanie_phase("beanie2", "beanie>=2,<3", "beanie2_probe"),
    "beanie1": lambda: beanie_phase("beanie1", "beanie<2", "beanie1_probe"),
    "wheelcheck": phase_wheelcheck,
    "cleanup": phase_cleanup,
}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    extra = sys.argv[2:]  # e.g. `run.py pymongo 4.9` runs one pin only
    for ph in (list(PHASES) if which == "all" else [which]):
        t0 = time.monotonic()
        if ph == "pymongo" and extra:
            phase_pymongo(extra)
        else:
            PHASES[ph]()
        print(f"phase {ph} done in {time.monotonic() - t0:.1f}s")
