"""driver-floors, engine 1.2.0 rerun: PyMongo AsyncMongoClient probe.

Runs inside ONE throwaway venv, always as `<venv>/bin/python -I probe_pymongo.py --db t_drivers --coll <name>`.
Reads LOCAL_URI from the environment and never prints it (any echo of it is replaced by ***).
Prints one JSON object on stdout with, in order:
  1. `from pymongo import AsyncMongoClient`
  2. async ping on admin and on the test database (the question under test)
  3. async server_info() (buildInfo as the driver sees it)
  4. EXTRA, beyond the spec: async insert_one / find_one / delete_one / count_documents on one collection
  5. sync MongoClient ping (control, so an async failure can be told apart from a connection failure)
Every driver error is recorded with type, code, codeName, errmsg and errorLabels when present, and every Python
warning raised during import and the calls is listed under "warnings"."""
import argparse
import asyncio
import importlib.metadata as md
import inspect
import json
import os
import sys
import time
import warnings

# Record every Python warning raised from here on (import of pymongo / AsyncMongoClient and all driver calls).
_wctx = warnings.catch_warnings(record=True)
WLIST = _wctx.__enter__()
warnings.simplefilter("always")

ap = argparse.ArgumentParser()
ap.add_argument("--db", required=True)
ap.add_argument("--coll", required=True)
args = ap.parse_args()

URI = os.environ.get("LOCAL_URI", "")
SECRETS = [s for s in (URI,) if s]


def scrub(x):
    s = str(x)
    for sec in SECRETS:
        s = s.replace(sec, "***")
    return s


def err(e):
    d = {"type": f"{type(e).__module__}.{type(e).__name__}", "str": scrub(e)}
    det = getattr(e, "details", None)
    if isinstance(det, dict):
        for k in ("ok", "code", "codeName", "errmsg", "errorLabels"):
            if k in det:
                d[k] = det[k]
    if "code" not in d and getattr(e, "code", None) is not None:
        d["code"] = e.code
    labels = getattr(e, "_error_labels", None)
    if labels:
        d["driver_error_labels"] = sorted(labels)
    return d


def dist(name):
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


out = {
    "python": sys.version.split()[0],
    "executable": sys.executable,
    "db": args.db,
    "coll": args.coll,
    "dist_versions": {n: dist(n) for n in ("pymongo", "dnspython", "motor", "pip")},
    "results": {},
}
R = out["results"]

import pymongo  # noqa: E402

out["pymongo.__version__"] = pymongo.__version__
try:
    out["pymongo.has_c()"] = pymongo.has_c()
except Exception as e:  # pragma: no cover
    out["pymongo.has_c()"] = repr(e)

# 1. import
try:
    from pymongo import AsyncMongoClient

    R["import_AsyncMongoClient"] = {
        "ok": True,
        "command": "from pymongo import AsyncMongoClient",
        "response": f"imported; class is {AsyncMongoClient.__module__}.{AsyncMongoClient.__qualname__}",
    }
except Exception as e:
    AsyncMongoClient = None
    R["import_AsyncMongoClient"] = {"ok": False, "command": "from pymongo import AsyncMongoClient", "error": err(e)}


async def maybe_await(x):
    if inspect.isawaitable(x):
        return await x
    return x


async def attempt(key, command, fn, store):
    t0 = time.monotonic()
    try:
        resp = await fn()
        store[key] = {"ok": True, "command": command, "response": resp}
    except Exception as e:
        store[key] = {"ok": False, "command": command, "error": err(e)}
    store[key]["elapsed_s"] = round(time.monotonic() - t0, 3)
    return store[key]


async def async_part():
    res = {}
    c = AsyncMongoClient(URI, serverSelectionTimeoutMS=15000)
    db = c[args.db]
    coll = db[args.coll]
    try:
        await attempt("async_ping_admin", "await AsyncMongoClient(LOCAL_URI, serverSelectionTimeoutMS=15000).admin.command('ping')",
                      lambda: c.admin.command("ping"), res)
        await attempt("async_ping_db", f"await client['{args.db}'].command('ping')",
                      lambda: db.command("ping"), res)

        async def si():
            info = await c.server_info()
            return {k: info.get(k) for k in ("version", "versionArray", "maxBsonObjectSize", "ok") if k in info}

        await attempt("async_server_info", "await client.server_info()  (keys version, versionArray, maxBsonObjectSize, ok)", si, res)

        # EXTRA (beyond the spec): a tiny async CRUD round trip so the async API is exercised past ping.
        crud = {}
        marker = {"probe": "async-crud", "pymongo": pymongo.__version__}

        async def ins():
            r = await coll.insert_one(dict(marker))
            crud["_id"] = r.inserted_id
            return {"acknowledged": r.acknowledged, "inserted_id": str(r.inserted_id)}

        async def fnd():
            d = await coll.find_one({"_id": crud.get("_id")})
            return {"found": d is not None, "doc": {k: str(v) for k, v in (d or {}).items()}}

        async def dele():
            r = await coll.delete_one({"_id": crud.get("_id")})
            return {"acknowledged": r.acknowledged, "deleted_count": r.deleted_count}

        async def cnt():
            return await coll.count_documents({})

        await attempt("insert_one", f"await client['{args.db}']['{args.coll}'].insert_one({json.dumps(marker)})", ins, crud)
        await attempt("find_one", f"await client['{args.db}']['{args.coll}'].find_one({{'_id': <inserted_id>}})", fnd, crud)
        await attempt("delete_one", f"await client['{args.db}']['{args.coll}'].delete_one({{'_id': <inserted_id>}})", dele, crud)
        await attempt("count_documents_after_delete", f"await client['{args.db}']['{args.coll}'].count_documents({{}})", cnt, crud)
        crud.pop("_id", None)
        res["extra_async_crud"] = crud
    finally:
        await maybe_await(c.close())
    return res


if AsyncMongoClient is not None:
    if not URI:
        R["async"] = {"ok": False, "error": "LOCAL_URI not set"}
    else:
        try:
            R.update(asyncio.run(async_part()))
        except Exception as e:
            R["async_unexpected"] = {"ok": False, "error": err(e)}
else:
    R["async_ping_admin"] = {
        "ok": None,
        "command": "await AsyncMongoClient(LOCAL_URI).admin.command('ping')",
        "response": "not attempted: AsyncMongoClient is not importable from this pymongo version",
    }

# 5. sync control
from pymongo import MongoClient  # noqa: E402

t0 = time.monotonic()
sc = MongoClient(URI, serverSelectionTimeoutMS=15000)
try:
    R["sync_ping_control"] = {"ok": True, "command": "MongoClient(LOCAL_URI, serverSelectionTimeoutMS=15000).admin.command('ping')",
                              "response": sc.admin.command("ping")}
except Exception as e:
    R["sync_ping_control"] = {"ok": False, "command": "MongoClient(LOCAL_URI).admin.command('ping')", "error": err(e)}
finally:
    sc.close()
R["sync_ping_control"]["elapsed_s"] = round(time.monotonic() - t0, 3)

out["warnings"] = [{"category": w.category.__name__, "message": scrub(w.message)[:500],
                    "where": f"{os.path.basename(str(w.filename))}:{w.lineno}"} for w in WLIST]
print(scrub(json.dumps(out, default=str)))
