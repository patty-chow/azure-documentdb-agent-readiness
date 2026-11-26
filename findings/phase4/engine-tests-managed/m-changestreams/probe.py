"""Pre-flight probe for m-changestreams: hello basics and whether mt_cs already exists. Read-only."""
import json, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from envload import ENV, j, scrub
from pymongo import MongoClient
c = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=20000, appname="m-changestreams-probe")
h = c.admin.command("hello")
out = {k: h.get(k) for k in ("isWritablePrimary", "maxWireVersion", "minWireVersion", "msg", "internal", "setName", "maxWriteBatchSize", "logicalSessionTimeoutMinutes")}
out["has_operationTime"] = "operationTime" in h
out["has_$clusterTime"] = "$clusterTime" in h
out["keys"] = sorted(h.keys())
out["mt_cs_exists"] = "mt_cs" in c.list_database_names()
print(scrub(json.dumps(j(out), indent=1, default=str)))
