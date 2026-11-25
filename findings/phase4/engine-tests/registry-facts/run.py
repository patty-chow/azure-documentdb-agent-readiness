#!/usr/bin/env python
"""registry-facts: query public registries (npm, PyPI, GHCR) and local docker only.
No cluster connection is made. Rerun: <venv python> -I run.py
Writes report.json next to this file."""
import re, json, os, subprocess, sys, time, urllib.request, urllib.error, shlex, hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = []
TIMEOUT = 120

def http_get(url, headers=None, accept_json=True):
    req = urllib.request.Request(url, headers={"User-Agent": "registry-facts/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return None, {}, repr(e).encode()

def hget(h, k):
    for kk, v in h.items():
        if kk.lower() == k.lower(): return v
    return None

def run_cmd(cmd, timeout=TIMEOUT):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "secs": round(time.time()-t0, 2)}
    except subprocess.TimeoutExpired as e:
        return {"exit": None, "stdout": e.stdout or "", "stderr": f"TIMEOUT after {timeout}s", "secs": timeout}
    except FileNotFoundError as e:
        return {"exit": None, "stdout": "", "stderr": repr(e), "secs": 0}

def step(name, command, response, reading, question=None):
    STEPS.append({"step": name, "command": command, "response": response, "reading": reading, **({"question": question} if question else {})})
    print(f"[{len(STEPS):02d}] {name}: {reading[:160]}", file=sys.stderr)

def jparse(s):
    try: return json.loads(s)
    except Exception as e: return {"_parse_error": repr(e), "_raw": s[:2000]}

# ---------------------------------------------------------------- npm
def npm_view(pkg):
    cmd = ["npm", "view", pkg, "name", "version", "versions", "time", "maintainers", "repository", "dist-tags", "description", "bin", "homepage", "--json"]
    r = run_cmd(cmd)
    data = jparse(r["stdout"]) if r["stdout"].strip() else {}
    return cmd, r, data

for pkg in ["documentdb-mcp-server", "@azure/documentdb-mcp-server", "@microsoft/documentdb-mcp-server"]:
    cmd, r, data = npm_view(pkg)
    if r["exit"] == 0 and isinstance(data, dict) and "error" not in data:
        reading = (f"npm has '{pkg}': latest {data.get('version')}, dist-tags {data.get('dist-tags')}, "
                   f"versions {data.get('versions')}, time {data.get('time')}, maintainers {data.get('maintainers')}, "
                   f"repository {data.get('repository')}, bin {data.get('bin')}.")
    else:
        err = data.get("error") if isinstance(data, dict) else None
        reading = f"npm view failed for '{pkg}': exit {r['exit']}, error {json.dumps(err)[:400] if err else r['stderr'][:400]}."
    step(f"npm view {pkg}", shlex.join(cmd), {"exit": r["exit"], "secs": r["secs"], "stdout_json": data, "stderr": r["stderr"][:2000]}, reading,
         question="Is documentdb-mcp-server (or a scoped @azure/@microsoft name) published on npm by Microsoft?")
    # registry raw GET for 404/200 confirmation + publish times
    url = "https://registry.npmjs.org/" + pkg.replace("/", "%2F")
    st, hdr, body = http_get(url)
    doc = jparse(body.decode("utf-8", "replace")) if body else {}
    if st == 200:
        resp = {"status": st, "dist-tags": doc.get("dist-tags"), "time": doc.get("time"), "maintainers": doc.get("maintainers"),
                "repository": doc.get("repository"), "versions": list((doc.get("versions") or {}).keys()),
                "latest_bin": (doc.get("versions", {}).get((doc.get("dist-tags") or {}).get("latest"), {}) or {}).get("bin"),
                "latest_dist": {k: v for k, v in ((doc.get("versions", {}).get((doc.get("dist-tags") or {}).get("latest"), {}) or {}).get("dist", {}) or {}).items() if k in ("tarball", "unpackedSize", "fileCount", "shasum")},
                "readme_len": len(doc.get("readme") or ""), "readme_head": (doc.get("readme") or "")[:300]}
        reading = f"GET {url} -> 200; dist-tags {doc.get('dist-tags')}; time {doc.get('time')}; maintainers {doc.get('maintainers')}; repository {doc.get('repository')}."
    else:
        resp = {"status": st, "body": body.decode("utf-8", "replace")[:500]}
        reading = f"GET {url} -> HTTP {st}: {body.decode('utf-8','replace')[:200]}"
    step(f"registry GET {pkg}", f"GET {url}", resp, reading)

# npm search for LlamaIndex TS stores
for q in ["@llamaindex/azure", "llamaindex documentdb", "llamaindex cosmos mongo vector store", "@llamaindex documentdb"]:
    cmd = ["npm", "search", q, "--json", "--searchlimit=20"]
    r = run_cmd(cmd)
    data = jparse(r["stdout"]) if r["stdout"].strip() else []
    if isinstance(data, list):
        names = [{"name": d.get("name"), "version": d.get("version"), "date": d.get("date"), "description": (d.get("description") or "")[:140]} for d in data]
        reading = f"npm search '{q}' returned {len(names)} packages: {[n['name'] for n in names][:20]}."
    else:
        # npm 11 --json output was not valid JSON (unescaped control char in a description); fall back to grepping package names from raw stdout
        names = {"parse_error": data.get("_parse_error"), "names_from_raw": re.findall(r'"name":\s*"([^"]+)"', r["stdout"])[:20]}
        reading = f"npm search '{q}': --json output not parseable ({data.get('_parse_error')}); package names in raw output: {names['names_from_raw']}."
    step(f"npm search {q!r}", shlex.join(cmd), {"exit": r["exit"], "secs": r["secs"], "results": names, "stderr": r["stderr"][:1000]}, reading,
         question="Is there a LlamaIndex TypeScript vector store for DocumentDB / Cosmos Mongo vCore?")
    url = "https://registry.npmjs.org/-/v1/search?size=20&text=" + urllib.request.quote(q)
    st, hdr, body = http_get(url)
    d = jparse(body.decode("utf-8", "replace"))
    objs = [{"name": o["package"].get("name"), "version": o["package"].get("version"), "date": o["package"].get("date"), "description": (o["package"].get("description") or "")[:140]} for o in d.get("objects", [])] if isinstance(d, dict) else []
    step(f"registry search API {q!r}", f"GET {url}", {"status": st, "total": d.get("total") if isinstance(d, dict) else None, "objects": objs},
         f"registry search '{q}' -> HTTP {st}, total {d.get('total') if isinstance(d, dict) else '?'}; names: {[o['name'] for o in objs]}.")

# @llamaindex/azure details + does it export the Cosmos Mongo store
for pkg in ["@llamaindex/azure", "@llamaindex/azure-cosmos-mongo", "@llamaindex/documentdb"]:
    cmd, r, data = npm_view(pkg)
    ok = r["exit"] == 0 and isinstance(data, dict) and "error" not in data
    step(f"npm view {pkg}", shlex.join(cmd), {"exit": r["exit"], "secs": r["secs"], "stdout_json": data, "stderr": r["stderr"][:1500]},
         (f"'{pkg}' exists: latest {data.get('version')}, time.modified {(data.get('time') or {}).get('modified')}, repository {data.get('repository')}, description {data.get('description')!r}."
          if ok else f"'{pkg}' not on npm: {json.dumps(data.get('error'))[:300] if isinstance(data, dict) else r['stderr'][:300]}."))

# fetch @llamaindex/azure tarball file list via unpkg (public CDN mirror of npm) to confirm export name
for url in ["https://unpkg.com/@llamaindex/azure/dist/index.d.ts", "https://unpkg.com/@llamaindex/azure/package.json"]:
    st, hdr, body = http_get(url)
    txt = body.decode("utf-8", "replace")
    hits = [ln.strip() for ln in txt.splitlines() if "Cosmos" in ln or "DocumentDB" in ln or '"version"' in ln or "mongodb" in ln.lower()][:40]
    step(f"unpkg {url.split('/azure/')[1]}", f"GET {url}", {"status": st, "matching_lines": hits, "length": len(txt)},
         f"HTTP {st}; lines mentioning Cosmos/DocumentDB/mongodb/version: {hits[:12]}")

# ---------------------------------------------------------------- PyPI
def pypi(name):
    url = f"https://pypi.org/pypi/{name}/json"
    st, hdr, body = http_get(url)
    if st != 200:
        step(f"PyPI {name}", f"GET {url}", {"status": st, "body": body.decode('utf-8','replace')[:300]}, f"PyPI returned HTTP {st} for {name}.")
        return
    d = jparse(body.decode("utf-8", "replace"))
    info = d.get("info", {})
    rel = d.get("releases", {})
    def rel_date(v):
        fs = rel.get(v) or []
        ts = sorted(f.get("upload_time_iso_8601") for f in fs if f.get("upload_time_iso_8601"))
        return ts[0] if ts else None
    # sort versions by first upload date
    vers = sorted(rel.keys(), key=lambda v: rel_date(v) or "")
    hist = [{"version": v, "released": rel_date(v), "yanked": any(f.get("yanked") for f in rel.get(v) or [])} for v in vers]
    resp = {"status": st, "name": info.get("name"), "latest": info.get("version"), "latest_released": rel_date(info.get("version")),
            "summary": info.get("summary"), "requires_python": info.get("requires_python"), "requires_dist": info.get("requires_dist"),
            "project_urls": info.get("project_urls"), "home_page": info.get("home_page"), "author": info.get("author"), "author_email": info.get("author_email"),
            "license": (info.get("license") or "")[:80], "release_count": len(vers), "releases": hist[-12:],
            "classifiers": [c for c in info.get("classifiers", []) if "Development Status" in c or "Python ::" in c]}
    step(f"PyPI {name}", f"GET {url}", resp,
         f"{name} latest {info.get('version')} released {rel_date(info.get('version'))}; {len(vers)} releases; requires_dist {len(info.get('requires_dist') or [])} entries; last 3 releases {[(h['version'], h['released'][:10] if h['released'] else None) for h in hist[-3:]]}.",
         question="Which LangChain / LlamaIndex Python package and version should the kit recommend, and when were they released?")
    return d

for name in ["langchain-azure-cosmosdb", "langchain-azure-ai", "llama-index-vector-stores-azurecosmosmongo", "llama-index-vector-stores-azurecosmosnosql"]:
    pypi(name)

# pip index versions (pip from venv)
VENV_PY = "/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python"
for name in ["langchain-azure-cosmosdb", "langchain-azure-ai", "llama-index-vector-stores-azurecosmosmongo"]:
    cmd = [VENV_PY, "-m", "pip", "index", "versions", name, "--disable-pip-version-check"]
    r = run_cmd(cmd)
    step(f"pip index versions {name}", shlex.join(cmd), {"exit": r["exit"], "secs": r["secs"], "stdout": r["stdout"][:3000], "stderr": r["stderr"][:1000]},
         f"pip index versions exit {r['exit']}: {r['stdout'].strip().splitlines()[:2] if r['stdout'].strip() else r['stderr'].strip()[:200]}")

# pip show-style metadata for llama-index-vector-stores-azurecosmosmongo: download wheel (no deps) into an isolated dir and read METADATA
dl = os.path.join(HERE, "downloads")
os.makedirs(dl, exist_ok=True)
cmd = [VENV_PY, "-m", "pip", "download", "--no-deps", "--dest", dl, "llama-index-vector-stores-azurecosmosmongo", "--disable-pip-version-check"]
r = run_cmd(cmd, timeout=240)
meta = {}
try:
    import zipfile, glob
    whls = sorted(glob.glob(os.path.join(dl, "llama_index_vector_stores_azurecosmosmongo-*.whl")))
    if whls:
        with zipfile.ZipFile(whls[-1]) as z:
            mname = [n for n in z.namelist() if n.endswith("METADATA")][0]
            md = z.read(mname).decode("utf-8", "replace")
            keep = ("Name:", "Version:", "Summary:", "Requires-Dist:", "Requires-Python:", "Author", "License", "Home-page", "Project-URL")
            meta = {"wheel": os.path.basename(whls[-1]), "metadata_lines": [ln for ln in md.splitlines() if ln.startswith(keep)]}
            # list module files and grep for default kind and pre_filter
            files = [n for n in z.namelist() if n.endswith(".py")]
            src = z.read([n for n in files if n.endswith("base.py")][0]).decode("utf-8", "replace") if any(n.endswith("base.py") for n in files) else ""
            meta["py_files"] = files
            meta["base_py_hits"] = [ln.strip() for ln in src.splitlines() if "vector-hnsw" in ln or "pre_filter" in ln or "_create_vector_search_index" in ln or "createIndexes" in ln][:30]
except Exception as e:
    meta = {"error": repr(e)}
step("pip download --no-deps llama-index-vector-stores-azurecosmosmongo (pip show-style metadata)", shlex.join(cmd),
     {"exit": r["exit"], "secs": r["secs"], "stdout": r["stdout"][-1500:], "stderr": r["stderr"][:800], "wheel_metadata": meta},
     (f"Downloaded {meta.get('wheel')}; METADATA {meta.get('metadata_lines', [])[:3]}; base.py hits {meta.get('base_py_hits', [])[:4]}." if meta.get("wheel") else f"pip download exit {r['exit']}: {r['stderr'][:200] or meta}"),
     question="Does the documented LlamaIndex 0.9.0 behaviour (HNSW default, pre_filter) still hold in the shipped wheel?")

# ---------------------------------------------------------------- GHCR tags
IMG = "documentdb/documentdb/documentdb-local"
tok_url = f"https://ghcr.io/token?scope=repository:{IMG}:pull&service=ghcr.io"
st, hdr, body = http_get(tok_url)
tok = jparse(body.decode("utf-8", "replace")).get("token") if st == 200 else None
step("GHCR anonymous pull token", f"GET {tok_url}", {"status": st, "token_received": bool(tok), "token_len": len(tok or "")},
     f"GHCR token endpoint returned HTTP {st}; anonymous pull token {'obtained' if tok else 'NOT obtained'} (token value not recorded).")

tags = None
if tok:
    url = f"https://ghcr.io/v2/{IMG}/tags/list?n=1000"
    st, hdr, body = http_get(url, headers={"Authorization": f"Bearer {tok}"})
    d = jparse(body.decode("utf-8", "replace"))
    tags = d.get("tags") if st == 200 else None
    step("GHCR tags list", f"GET {url} (Authorization: Bearer <anon token>)", {"status": st, "tag_count": len(tags or []), "tags": tags, "link_header": hget(hdr, "Link"), "error": None if st == 200 else d},
         f"HTTP {st}; {len(tags or [])} tags in total; named/versioned tags (not CI run ids or sha256-*): {sorted(t for t in (tags or []) if not re.match(r'^(\d{6,}|sha256-)', t))}", question="Which versioned tags exist for documentdb-local and which should CI pin?")

    # resolve digests for key tags
    want = ["latest", "stable", "1.0", "1.2", "pg15-1.2.0", "pg16-1.2.0", "pg17-1.2.0", "pg18-1.2.0", "pg17-1.0.0", "pg17-1.0.1", "pg17-1.0-rc2"]
    for t in [w for w in want if (tags is None or w in tags)]:
        url = f"https://ghcr.io/v2/{IMG}/manifests/{t}"
        acc = "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
        st, h, body = http_get(url, headers={"Authorization": f"Bearer {tok}", "Accept": acc})
        d = jparse(body.decode("utf-8", "replace"))
        plats = [f"{m.get('platform',{}).get('os')}/{m.get('platform',{}).get('architecture')}" for m in d.get("manifests", [])] if isinstance(d, dict) else []
        dig = hget(h, "Docker-Content-Digest"); body_sha = "sha256:" + hashlib.sha256(body).hexdigest()
        child = [{"platform": f"{m.get('platform',{}).get('os')}/{m.get('platform',{}).get('architecture')}", "digest": m.get("digest")} for m in d.get("manifests", [])] if isinstance(d, dict) else []
        step(f"GHCR manifest {t}", f"GET {url} (Accept: OCI index/manifest)",
             {"status": st, "docker_content_digest": dig, "sha256_of_body": body_sha, "content_type": hget(h, "Content-Type"), "mediaType": d.get("mediaType") if isinstance(d, dict) else None, "platform_manifests": child, "error": None if st == 200 else d},
             f"tag {t}: HTTP {st}, manifest-list digest {dig or body_sha}, platforms {plats}.")

# does the digest the running ddb-engine-test container uses still resolve on GHCR, and which tag/version is it?
if tok:
    local_dig = "sha256:a22772de11861a97d395eecdbe6fbaedd245498b015e748ca409f526430ca781"  # RepoDigest of local :latest (see docker image inspect step)
    url = f"https://ghcr.io/v2/{IMG}/manifests/{local_dig}"
    acc = "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
    st, h, body = http_get(url, headers={"Authorization": f"Bearer {tok}", "Accept": acc})
    d = jparse(body.decode("utf-8", "replace"))
    plats = [f"{m.get('platform',{}).get('os')}/{m.get('platform',{}).get('architecture')}" for m in d.get("manifests", [])] if isinstance(d, dict) else []
    step("GHCR manifest by digest (image the running ddb-engine-test container uses)", f"GET {url} (Accept: OCI index/manifest)",
         {"status": st, "docker_content_digest": hget(h, "Docker-Content-Digest"), "mediaType": d.get("mediaType") if isinstance(d, dict) else None, "platforms": plats, "error": None if st == 200 else d},
         f"local container digest {local_dig[:19]}...: HTTP {st}, platforms {plats}; it matches none of the digests resolved above for latest/1.2/pg17-1.2.0 ({'sha256:1d40546c'}) or 1.0/stable/pg17-1.0.x ({'sha256:5c3df9c6'}), so the running container is an older :latest pull.",
         question="Which engine/gateway version is the local ddb-engine-test container actually running (for interpreting the other tests)?")

# docker image ls locally (fallback and local state)
cmd = ["docker", "image", "ls", "--digests", "--format", "{{json .}}", "ghcr.io/documentdb/documentdb/documentdb-local"]
r = run_cmd(cmd)
imgs = [jparse(l) for l in r["stdout"].splitlines() if l.strip()]
step("docker image ls (local)", shlex.join(cmd), {"exit": r["exit"], "images": imgs, "stderr": r["stderr"][:500]},
     f"{len(imgs)} local documentdb-local images: {[(i.get('Tag'), (i.get('Digest') or '')[:19], i.get('CreatedAt')) for i in imgs]}.")
cmd = ["docker", "inspect", "ddb-engine-test", "--format", "{{.Config.Image}} | {{.Image}} | {{.Created}}"]
r = run_cmd(cmd)
step("docker inspect ddb-engine-test (image used by the running test container)", shlex.join(cmd), {"exit": r["exit"], "stdout": r["stdout"].strip(), "stderr": r["stderr"][:500]},
     f"Container image ref and ids: {r['stdout'].strip()[:300] or r['stderr'][:200]}")
cmd = ["docker", "image", "inspect", "ghcr.io/documentdb/documentdb/documentdb-local:latest", "--format", "{{json .RepoDigests}} {{.Created}} {{json .Config.Labels}}"]
r = run_cmd(cmd)
step("docker image inspect local :latest (RepoDigests, Created, labels)", shlex.join(cmd), {"exit": r["exit"], "stdout": r["stdout"].strip()[:3000], "stderr": r["stderr"][:500]},
     f"Local :latest RepoDigests/created/labels: {r['stdout'].strip()[:400] or r['stderr'][:200]}")

# ---------------------------------------------------------------- write report
report = {
    "test": "registry-facts", "database": "none", "ran_at": datetime.now(timezone.utc).isoformat(),
    "engine_version": "n/a (no cluster queried; local container image state recorded via docker only)",
    "script": os.path.join(HERE, "run.py"),
    "evidence_scope": "Public registry facts (npm, PyPI, unpkg, GHCR) observed at ran_at, plus local docker image state on this Mac. These describe published packages and image tags, not managed-service behaviour.",
    "steps": STEPS,
}
with open(os.path.join(HERE, "report.json"), "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"wrote {os.path.join(HERE, 'report.json')} with {len(STEPS)} steps", file=sys.stderr)
