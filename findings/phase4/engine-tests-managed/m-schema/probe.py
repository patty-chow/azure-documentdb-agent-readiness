"""Connectivity probe for m-schema: prints hello keys and hello.internal only (no secrets)."""
import json, os, re, warnings
warnings.filterwarnings("ignore", message=".*CosmosDB.*")
from pymongo import MongoClient
from bson import json_util

HERE = os.path.dirname(os.path.abspath(__file__))
env = {}
for line in open(os.path.join(HERE, "..", "managed.env")):
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k.replace("export ", "").strip()] = v.strip().strip('"').strip("'")
c = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, appname="m-schema-probe")
h = c.admin.command("hello")
print("hello keys:", sorted(h.keys()))
print("internal:", json_util.dumps(h.get("internal")))
print("maxWireVersion:", h.get("maxWireVersion"), "msg:", h.get("msg"))
bi = c.admin.command("buildInfo")
print("buildInfo keys:", sorted(bi.keys()))
print("buildInfo version:", bi.get("version"), bi.get("versionArray"))
c.close()
