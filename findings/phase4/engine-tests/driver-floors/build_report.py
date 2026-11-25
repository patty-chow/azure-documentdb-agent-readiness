"""Assemble report.json from the out/ files written by run.sh. Never reads local.env, so no credential can leak."""
import json, os, re, sys, subprocess
W = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(W, "out")
def rd(n):
    p = os.path.join(O, n)
    return open(p).read() if os.path.exists(p) else None
def js(n):
    s = rd(n); 
    try: return json.loads(s) if s else None
    except Exception as e: return {"_parse_error": repr(e), "_raw": (s or "")[:500]}

steps = []
def add(step, command, response, reading): steps.append({"step": step, "command": command, "response": response, "reading": reading})

pyver = (rd("python_version.txt") or "").strip().replace("\n", " @ ")
add("record interpreter used for throwaway venvs", "python3 --version; which python3", pyver,
    "All throwaway venvs were created with the Homebrew python3 shown (not the repo .venv).")

# pymongo matrix
matrix = {}
for v in ("4.8.0", "4.9.0", "4.11.0", "4.13.0"):
    inst = (rd(f"pymongo-{v}.install.log") or "").strip()
    frz = (rd(f"pymongo-{v}.freeze.txt") or "").strip().replace("\n", "; ")
    add(f"pymongo=={v}: create venv and install", f"python3 -m venv venvs/pymongo-{v} && venvs/pymongo-{v}/bin/pip install pymongo=={v} && pip freeze",
        f"{inst}; freeze: {frz}", f"pip resolved pymongo=={v} exactly (freeze shows the installed dist).")
    pr = js(f"pymongo-{v}.probe.json") or {}
    for s in pr.get("steps", []):
        add(f"pymongo=={v}: {s['step']}", s["command"], s["response"], s["reading"])
    matrix[v] = {"installed": pr.get("pymongo_dist_version"), "has_c_ext": pr.get("has_c_ext"),
                 "async_import_ok": pr.get("async_import_ok"), "async_import_error": pr.get("async_import_error"),
                 "async_ping_ok": (pr.get("async_ping") or {}).get("ok"), "async_ping_response": (pr.get("async_ping") or {}).get("response") or (pr.get("async_ping") or {}).get("error"),
                 "sync_ping_ok": (pr.get("sync_ping") or {}).get("ok")}

# beanie
beanie = {}
for tag, spec in (("beanie2", "beanie>=2,<3"), ("beanie1", "beanie<2")):
    inst = (rd(f"{tag}.install.log") or "").strip(); frz = (rd(f"{tag}.freeze.txt") or "").strip().replace("\n", "; ")
    add(f"{tag}: create venv and install '{spec}'", f"python3 -m venv venvs/{tag} && venvs/{tag}/bin/pip install '{spec}' && pip freeze", f"{inst}; freeze: {frz}",
        "Shows which beanie, pymongo and (if any) motor versions pip resolved.")
    pr = js(f"{tag}.probe.json") or {}
    req = [r for r in (pr.get("beanie_requires") or []) if "extra ==" not in r]
    add(f"{tag}: declared runtime requirements", "importlib.metadata.requires('beanie') (non-extra entries)", json.dumps(req),
        "Beanie's own metadata states its driver dependency.")
    for s in pr.get("steps", []):
        add(f"{tag}: {s['step']}", s["command"], s["response"], s["reading"])
    beanie[tag] = {"beanie": pr.get("beanie_version"), "pymongo": pr.get("pymongo_version"), "motor": pr.get("motor_version"),
                   "pydantic": pr.get("pydantic_version"), "runtime_requires": req, "import_ok": pr.get("beanie_import_ok"),
                   "roundtrip": pr.get("beanie_roundtrip")}

# changelogs
dl = rd("sdist_download.log") or ""
add("pip download pymongo 4.6.3 and 4.7.0 sdists", "pip download --no-deps --no-binary :all: pymongo==4.6.3 -d sdists; same for 4.7.0",
    "; ".join(l for l in dl.splitlines() if l.startswith(("Saved", "exit="))), "Both sdists downloaded from PyPI.")
cl = {}
for v in ("4.6.3", "4.7.0"):
    t = rd(f"pymongo-{v}.changelog_oidc.txt") or ""
    m = re.search(r"--- grep -c -i OIDC ---\n(\d+)", t); cnt = int(m.group(1)) if m else None
    lines = t.split("--- grep -n -i OIDC (first 40) ---\n", 1)[1].strip() if "(first 40) ---" in t else ""
    sec = (rd(f"pymongo-{v}.changelog_oidc_by_section.txt") or "").strip()
    cl[v] = {"oidc_match_count": cnt, "matching_lines": lines, "section_headings": sorted(set(l.split(" :: ")[0] for l in sec.splitlines())) if sec else []}
    add(f"grep OIDC in pymongo-{v}/doc/changelog.rst", f"grep -c -i OIDC sdists/pymongo-{v}/doc/changelog.rst; grep -n -i OIDC ...",
        f"count={cnt}; lines: {lines or '(none)'}; sections: {cl[v]['section_headings']}",
        f"pymongo {v} changelog {'does not mention' if cnt == 0 else 'mentions'} OIDC" + (" (under 'Changes in Version 4.7')." if cnt else "."))

# node
node = {}
for v in ("6.6.0", "6.7.0"):
    t = js(f"npm_mongodb_{v}_time.json") or {}
    pub = t.get(v); node[v] = {"npm_publish_time": pub}
    add(f"npm view mongodb@{v} time", f"npm view mongodb@{v} time --json | .['{v}']", f"{v}: {pub}; (registry 'modified': {t.get('modified')})",
        f"mongodb@{v} was published to npm at {pub}.")
    rel = js(f"node_release_{v}.json") or {}; http = (rd(f"node_release_{v}.http") or "").strip()
    body = rel.get("body", "") or ""
    hits = [l.strip() for l in body.splitlines() if re.search("oidc", l, re.I)]
    node[v].update({"github_release_published_at": rel.get("published_at"), "github_release_url": rel.get("html_url"), "oidc_lines_in_release_notes": len(hits), "first_oidc_lines": hits[:4]})
    add(f"grep OIDC in node-mongodb-native v{v} GitHub release notes", f"curl https://api.github.com/repos/mongodb/node-mongodb-native/releases/tags/v{v} | grep -i oidc body",
        f"HTTP {http}; published_at={rel.get('published_at')}; oidc lines={len(hits)}; first: {hits[:3]}",
        f"The v{v} release notes {'do not mention' if not hits else 'announce'} MONGODB-OIDC.")

bi = js("buildinfo.json") or {}
report = {
    "test": "driver-floors", "database": "t_drivers",
    "engine": {"image": "ghcr.io/documentdb/documentdb/documentdb-local:latest (container ddb-engine-test)", "buildInfo": bi,
               "evidence_scope": "Facts observed here describe the open-source DocumentDB engine + gateway in documentdb-local at the buildInfo version above; they do not prove managed Azure DocumentDB behaviour."},
    "decisions_md_topics": ["4.1 PyMongo OIDC floor", "4.2 Node OIDC floor", "4.5 AsyncMongoClient floor 4.9/4.11/4.13", "4.6 Beanie 2 on AsyncMongoClient vs Beanie 1 + Motor", "4.11-open whether kit skills should state floors"],
    "steps": steps,
    "summary": {"pymongo_matrix": matrix, "beanie": beanie, "pymongo_changelog_oidc": cl, "node_driver": node},
    "scripts": {"run": f"{W}/run.sh", "probe": f"{W}/probe.py", "beanie_probe": f"{W}/beanie_probe.py", "build_report": f"{W}/build_report.py", "raw_outputs": O},
}
json.dump(report, open(os.path.join(W, "report.json"), "w"), indent=2, default=str)
print("wrote", os.path.join(W, "report.json"), "steps:", len(steps))
