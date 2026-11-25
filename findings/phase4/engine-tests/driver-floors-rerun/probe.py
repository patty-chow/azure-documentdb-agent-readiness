"""Run inside a throwaway venv. Reads LOCAL_URI from the environment (never prints it).
Records: pymongo version, whether `from pymongo import AsyncMongoClient` works, and whether an async ping succeeds.
Also runs a sync ping as a control. Writes JSON to stdout."""
import asyncio, json, os, sys, traceback, importlib.metadata as md

out = {"python": sys.version.split()[0], "steps": []}
uri = os.environ.get("LOCAL_URI")
db_name = "t_drivers_rerun"

def step(name, cmd, resp, reading):
    out["steps"].append({"step": name, "command": cmd, "response": resp, "reading": reading})

try:
    import pymongo
    out["pymongo_version"] = pymongo.__version__
    out["pymongo_dist_version"] = md.version("pymongo")
    try:
        out["has_c_ext"] = pymongo.has_c()
    except Exception as e:
        out["has_c_ext"] = f"unknown: {e!r}"
except Exception as e:
    out["pymongo_import_error"] = repr(e)
    print(json.dumps(out)); sys.exit(0)

# 1. import AsyncMongoClient
try:
    from pymongo import AsyncMongoClient  # noqa
    out["async_import_ok"] = True
    step("import AsyncMongoClient", "from pymongo import AsyncMongoClient", "ok (name importable)",
         f"pymongo {out['pymongo_version']} exposes AsyncMongoClient.")
except Exception as e:
    out["async_import_ok"] = False
    out["async_import_error"] = repr(e)
    step("import AsyncMongoClient", "from pymongo import AsyncMongoClient", repr(e),
         f"pymongo {out['pymongo_version']} has no AsyncMongoClient (async API not present).")

def err_detail(e):
    d = {"type": type(e).__name__, "str": str(e)}
    det = getattr(e, "details", None)
    if isinstance(det, dict):
        for k in ("code", "codeName", "errmsg", "errorLabels"):
            if k in det: d[k] = det[k]
    return d

# 2. async ping (if available)
if out["async_import_ok"] and uri:
    async def aping():
        from pymongo import AsyncMongoClient
        c = AsyncMongoClient(uri, serverSelectionTimeoutMS=10000)
        try:
            r = await c.admin.command("ping")
            r2 = await c[db_name].command("ping")
            return {"admin_ping": r, "t_drivers_rerun_ping": r2}
        finally:
            await c.close()
    try:
        r = asyncio.run(aping())
        out["async_ping"] = {"ok": True, "response": r}
        step("async ping", "await AsyncMongoClient(LOCAL_URI).admin.command('ping'); await client['t_drivers_rerun'].command('ping')",
             json.dumps(r, default=str), f"Async ping against documentdb-local succeeded with pymongo {out['pymongo_version']}.")
    except Exception as e:
        out["async_ping"] = {"ok": False, "error": err_detail(e), "trace": traceback.format_exc()[-1500:]}
        step("async ping", "await AsyncMongoClient(LOCAL_URI).admin.command('ping')", json.dumps(err_detail(e), default=str),
             f"Async ping failed with pymongo {out['pymongo_version']}.")
elif uri:
    step("async ping", "await AsyncMongoClient(LOCAL_URI).admin.command('ping')", "not attempted: AsyncMongoClient not importable",
         "No async client in this pymongo version, so no async ping possible.")

# 3. sync ping control
if uri:
    try:
        from pymongo import MongoClient
        c = MongoClient(uri, serverSelectionTimeoutMS=10000)
        r = c.admin.command("ping"); c.close()
        out["sync_ping"] = {"ok": True, "response": r}
        step("sync ping (control)", "MongoClient(LOCAL_URI).admin.command('ping')", json.dumps(r, default=str),
             f"Sync ping succeeded with pymongo {out['pymongo_version']} (control for the async result).")
    except Exception as e:
        out["sync_ping"] = {"ok": False, "error": err_detail(e)}
        step("sync ping (control)", "MongoClient(LOCAL_URI).admin.command('ping')", json.dumps(err_detail(e), default=str),
             "Sync ping failed.")
print(json.dumps(out, default=str))
