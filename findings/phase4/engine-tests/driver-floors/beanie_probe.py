"""Run inside a beanie venv. Records installed beanie/pymongo/motor versions, beanie import, and (for 2.x) init_beanie against t_drivers."""
import asyncio, json, os, sys, traceback, importlib.metadata as md
out = {"python": sys.version.split()[0], "steps": []}
for d in ("beanie", "pymongo", "motor", "pydantic"):
    try: out[f"{d}_version"] = md.version(d)
    except md.PackageNotFoundError: out[f"{d}_version"] = None
try:
    reqs = md.requires("beanie") or []
    out["beanie_requires"] = reqs
except Exception as e:
    out["beanie_requires"] = repr(e)
try:
    import beanie
    out["beanie_import_ok"] = True
    out["steps"].append({"step": "import beanie", "command": "import beanie", "response": f"ok, beanie {out['beanie_version']}",
                         "reading": f"beanie {out['beanie_version']} imports with pymongo {out['pymongo_version']}, motor {out['motor_version']}."})
except Exception as e:
    out["beanie_import_ok"] = False; out["beanie_import_error"] = repr(e)
    out["steps"].append({"step": "import beanie", "command": "import beanie", "response": repr(e), "reading": "beanie failed to import."})
    print(json.dumps(out, default=str)); sys.exit(0)

uri = os.environ.get("LOCAL_URI")
if uri and out["beanie_version"] and out["beanie_version"].startswith("2"):
    async def run():
        from pymongo import AsyncMongoClient
        from beanie import Document, init_beanie
        class Probe(Document):
            name: str
            class Settings:
                name = "beanie_probe"
        c = AsyncMongoClient(uri, serverSelectionTimeoutMS=10000)
        try:
            await init_beanie(database=c["t_drivers"], document_models=[Probe])
            doc = await Probe(name="hello").insert()
            got = await Probe.find_one(Probe.name == "hello")
            n = await Probe.count()
            await Probe.find_all().delete()
            return {"inserted_id": str(doc.id), "found": got is not None, "count_after_insert": n}
        finally:
            await c.close()
    try:
        r = asyncio.run(run())
        out["beanie_roundtrip"] = {"ok": True, "response": r}
        out["steps"].append({"step": "beanie 2 init_beanie + insert/find on t_drivers", "command": "init_beanie(database=AsyncMongoClient(LOCAL_URI)['t_drivers'], document_models=[Probe]); Probe(name='hello').insert(); Probe.find_one(...); Probe.count(); Probe.find_all().delete()", "response": json.dumps(r), "reading": "Beanie 2 on AsyncMongoClient works end-to-end against documentdb-local."})
    except Exception as e:
        det = {"type": type(e).__name__, "str": str(e)}
        d = getattr(e, "details", None)
        if isinstance(d, dict):
            for k in ("code","codeName","errmsg","errorLabels"):
                if k in d: det[k] = d[k]
        out["beanie_roundtrip"] = {"ok": False, "error": det, "trace": traceback.format_exc()[-1500:]}
        out["steps"].append({"step": "beanie 2 init_beanie + insert/find on t_drivers", "command": "init_beanie(... AsyncMongoClient ...)", "response": json.dumps(det, default=str), "reading": "Beanie 2 roundtrip failed against documentdb-local."})
elif uri and out["beanie_version"]:
    # beanie 1.x: check that it needs motor by trying init with a motor client
    async def run():
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import Document, init_beanie
        class Probe(Document):
            name: str
            class Settings:
                name = "beanie1_probe"
        c = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
        try:
            await init_beanie(database=c["t_drivers"], document_models=[Probe])
            doc = await Probe(name="hello").insert()
            n = await Probe.count()
            await Probe.find_all().delete()
            return {"inserted_id": str(doc.id), "count_after_insert": n}
        finally:
            c.close()
    try:
        r = asyncio.run(run())
        out["beanie_roundtrip"] = {"ok": True, "response": r}
        out["steps"].append({"step": "beanie 1 init_beanie via Motor on t_drivers", "command": "init_beanie(database=AsyncIOMotorClient(LOCAL_URI)['t_drivers'], ...)", "response": json.dumps(r), "reading": "Beanie 1 on Motor works against documentdb-local."})
    except Exception as e:
        det = {"type": type(e).__name__, "str": str(e)}
        out["beanie_roundtrip"] = {"ok": False, "error": det, "trace": traceback.format_exc()[-1500:]}
        out["steps"].append({"step": "beanie 1 init_beanie via Motor on t_drivers", "command": "init_beanie(... AsyncIOMotorClient ...)", "response": json.dumps(det), "reading": "Beanie 1 roundtrip failed."})
print(json.dumps(out, default=str))
