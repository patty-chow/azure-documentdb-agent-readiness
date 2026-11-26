"""Connectivity probe for m-txn-bulk: hello, buildInfo, topology. Prints only redacted output."""
import json
import sys
from pymongo import MongoClient
sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import ENV, jsonable, redact

c = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000)
h = c.admin.command("hello")
bi = c.admin.command("buildInfo")
td = c.topology_description
print(json.dumps({
    "hello": jsonable(h),
    "buildInfo": jsonable({k: bi.get(k) for k in ("version", "versionArray", "gitVersion", "modules", "ok")}),
    "topology_type": td.topology_type_name,
    "servers": [{"address": redact(str(a)), "type": s.server_type_name} for a, s in td.server_descriptions().items()],
}, indent=1, default=str))
c.close()
