"""driver-floors, engine 1.2.0 rerun: Beanie probe.

Runs inside ONE throwaway venv, always as `<venv>/bin/python -I probe_beanie.py --db t_drivers --coll <name>`.
Beanie >= 2 is driven through pymongo.AsyncMongoClient and Beanie 1.x through motor.motor_asyncio.AsyncIOMotorClient,
which is the client each major line documents. Steps on one collection:
  init_beanie -> index_information -> insert -> find_one (indexed field) -> find().to_list() -> get(id) -> delete -> count
  EXTRA: a second init_beanie from a NEW client on the same, now existing, collection (what an app restart does),
         then index_information again; then a third init with allow_index_dropping=True.
Also records installed versions, Beanie's declared runtime requirements, whether `motor` is importable, every Python
warning (with its file path relative to site-packages), and the wire commands the client sent and the replies it got
(pymongo command monitoring; only an allowlist of data/index commands is kept, so no authentication payload is stored).
Reads LOCAL_URI from the environment and never prints it."""
import argparse
import asyncio
import importlib.metadata as md
import inspect
import json
import os
import sys
import sysconfig
import time
import warnings

ap = argparse.ArgumentParser()
ap.add_argument("--db", required=True)
ap.add_argument("--coll", required=True)
args = ap.parse_args()
URI = os.environ.get("LOCAL_URI", "")
SITE = sysconfig.get_paths().get("purelib", "")


def scrub(x):
    s = str(x)
    return s.replace(URI, "***") if URI else s


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


def relpath(p):
    p = str(p)
    if SITE and p.startswith(SITE):
        return "site-packages/" + os.path.relpath(p, SITE)
    return p


out = {"python": sys.version.split()[0], "executable": sys.executable, "db": args.db, "coll": args.coll,
       "results": {}, "wire": []}
R = out["results"]
PHASE = {"name": "setup"}
KEEP = {"listIndexes", "createIndexes", "dropIndexes", "insert", "find", "delete", "update", "aggregate", "count",
        "listCollections", "create", "drop", "ping", "buildInfo"}
DROP_KEYS = {"lsid", "$clusterTime", "$readPreference", "txnNumber", "signature"}

with warnings.catch_warnings(record=True) as wlist:
    warnings.simplefilter("always")

    out["dist_versions"] = {n: dist(n) for n in ("beanie", "pymongo", "motor", "pydantic", "pydantic_core", "lazy-model", "dnspython")}
    try:
        reqs = md.requires("beanie") or []
        out["beanie_requires_runtime"] = [r for r in reqs if "extra ==" not in r]
    except md.PackageNotFoundError as e:
        out["beanie_requires_runtime"] = repr(e)

    try:
        import motor  # noqa: F401
        R["import_motor"] = {"ok": True, "command": "import motor", "response": f"imported motor {getattr(motor, 'version', '?')}"}
    except Exception as e:
        R["import_motor"] = {"ok": False, "command": "import motor", "error": err(e)}

    try:
        import beanie
        from beanie import Document, Indexed, init_beanie
        R["import_beanie"] = {"ok": True, "command": "import beanie; from beanie import Document, Indexed, init_beanie",
                              "response": f"imported beanie {beanie.__version__}"}
    except Exception as e:
        R["import_beanie"] = {"ok": False, "command": "import beanie", "error": err(e)}
        beanie = None

    if beanie is not None:
        from pymongo import monitoring

        class Listener(monitoring.CommandListener):
            def _doc(self, d):
                return {k: v for k, v in dict(d).items() if k not in DROP_KEYS}

            def started(self, event):
                if event.command_name in KEEP:
                    out["wire"].append({"phase": PHASE["name"], "event": "started", "request_id": event.request_id,
                                        "command_name": event.command_name, "command": self._doc(event.command)})

            def succeeded(self, event):
                if event.command_name in KEEP:
                    out["wire"].append({"phase": PHASE["name"], "event": "succeeded", "request_id": event.request_id,
                                        "command_name": event.command_name, "reply": self._doc(event.reply)})

            def failed(self, event):
                if event.command_name in KEEP:
                    out["wire"].append({"phase": PHASE["name"], "event": "failed", "request_id": event.request_id,
                                        "command_name": event.command_name, "failure": self._doc(event.failure)})

        LISTENER = Listener()
        major = int(str(beanie.__version__).split(".")[0])
        out["beanie_major"] = major
        COLL = args.coll

        class Probe(Document):
            name: Indexed(str)
            n: int = 0

            class Settings:
                name = COLL

        if major >= 2:
            client_ctor = "pymongo.AsyncMongoClient(LOCAL_URI, serverSelectionTimeoutMS=15000, event_listeners=[listener])"
        else:
            client_ctor = "motor.motor_asyncio.AsyncIOMotorClient(LOCAL_URI, serverSelectionTimeoutMS=15000, event_listeners=[listener])"
        out["client_ctor"] = client_ctor

        def new_client():
            if major >= 2:
                from pymongo import AsyncMongoClient
                return AsyncMongoClient(URI, serverSelectionTimeoutMS=15000, event_listeners=[LISTENER])
            from motor.motor_asyncio import AsyncIOMotorClient
            return AsyncIOMotorClient(URI, serverSelectionTimeoutMS=15000, event_listeners=[LISTENER])

        async def close(c):
            closed = c.close()  # sync for Motor, a coroutine for AsyncMongoClient
            if inspect.isawaitable(closed):
                await closed

        async def attempt(key, command, fn):
            PHASE["name"] = key
            t0 = time.monotonic()
            try:
                R[key] = {"ok": True, "command": command, "response": await fn()}
            except Exception as e:
                R[key] = {"ok": False, "command": command, "error": err(e)}
            R[key]["elapsed_s"] = round(time.monotonic() - t0, 3)
            PHASE["name"] = "between"
            return R[key]["ok"]

        async def roundtrip():
            client = new_client()
            out["client_class"] = f"{type(client).__module__}.{type(client).__qualname__}"
            state = {}
            try:
                async def do_init():
                    r = await init_beanie(database=client[args.db], document_models=[Probe])
                    return f"returned {r!r}"

                ok = await attempt("init_beanie",
                                   f"await init_beanie(database={client_ctor}['{args.db}'], document_models=[Probe])"
                                   f"  # Probe(Document): name: Indexed(str); n: int = 0; Settings.name = '{COLL}'",
                                   do_init)
                if not ok:
                    return

                async def idx():
                    return await client[args.db][COLL].index_information()

                await attempt("index_information_after_init", f"await client['{args.db}']['{COLL}'].index_information()", idx)

                async def ins():
                    p = Probe(name="hello", n=1)
                    r = await p.insert()
                    state["id"] = p.id
                    return {"inserted_id": str(p.id), "returned_type": type(r).__name__}

                if not await attempt("insert", "await Probe(name='hello', n=1).insert()", ins):
                    return

                async def f1():
                    d = await Probe.find_one(Probe.name == "hello")
                    return {"found": d is not None, "id_matches": d is not None and d.id == state["id"],
                            "doc": None if d is None else {"name": d.name, "n": d.n}}

                await attempt("find_one", "await Probe.find_one(Probe.name == 'hello')", f1)

                async def f2():
                    lst = await Probe.find(Probe.n >= 1).to_list()
                    return {"count": len(lst), "names": [d.name for d in lst]}

                await attempt("find_to_list", "await Probe.find(Probe.n >= 1).to_list()", f2)

                async def g():
                    d = await Probe.get(state["id"])
                    return {"found": d is not None}

                await attempt("get_by_id", "await Probe.get(<inserted id>)", g)

                async def dl():
                    d = await Probe.get(state["id"])
                    r = await d.delete()
                    return {"deleted_count": getattr(r, "deleted_count", None), "returned_type": type(r).__name__}

                await attempt("delete", "await (await Probe.get(<inserted id>)).delete()", dl)

                async def c2():
                    return await Probe.find_all().count()

                await attempt("count_after_delete", "await Probe.find_all().count()", c2)
            finally:
                await close(client)

            # EXTRA: second init_beanie from a brand-new client on the existing collection (an app restart).
            async def reinit():
                c2 = new_client()
                try:
                    r = await init_beanie(database=c2[args.db], document_models=[Probe])
                    info = await c2[args.db][COLL].index_information()
                    n = await Probe.find_all().count()
                    return {"init_beanie_returned": repr(r), "index_information_after": info, "count_after": n}
                finally:
                    await close(c2)

            await attempt("init_beanie_again_new_client",
                          f"c2 = {client_ctor}; await init_beanie(database=c2['{args.db}'], document_models=[Probe]); "
                          f"await c2['{args.db}']['{COLL}'].index_information(); await Probe.find_all().count()",
                          reinit)

            # EXTRA: a third init from a new client with allow_index_dropping=True. Beanie compares every index option
            # except key and v, so a server-added option (storageEngine) makes the existing index look different.
            async def reinit_drop():
                c3 = new_client()
                try:
                    r = await init_beanie(database=c3[args.db], document_models=[Probe], allow_index_dropping=True)
                    info = await c3[args.db][COLL].index_information()
                    return {"init_beanie_returned": repr(r), "index_information_after": info}
                finally:
                    await close(c3)

            await attempt("init_beanie_allow_index_dropping_new_client",
                          f"c3 = {client_ctor}; await init_beanie(database=c3['{args.db}'], document_models=[Probe], "
                          f"allow_index_dropping=True); await c3['{args.db}']['{COLL}'].index_information()",
                          reinit_drop)

        try:
            asyncio.run(roundtrip())
        except Exception as e:
            R["roundtrip_unexpected"] = {"ok": False, "error": err(e)}

    for w in wlist:
        out.setdefault("warnings", []).append({"category": w.category.__name__, "message": scrub(w.message)[:500],
                                               "where": f"{relpath(w.filename)}:{w.lineno}"})

out.setdefault("warnings", [])
print(scrub(json.dumps(out, default=str)))
