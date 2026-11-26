import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ENV, to_jsonable, redact
import json
from pymongo import MongoClient
c = MongoClient(ENV["MANAGED_URI"], serverSelectionTimeoutMS=30000, connectTimeoutMS=20000)
h = c.admin.command("hello")
print("hello keys", sorted(h.keys()))
sel = {k: h.get(k) for k in ("msg", "isWritablePrimary", "ismaster", "secondary", "setName", "hosts", "me",
                             "maxWireVersion", "minWireVersion", "maxWriteBatchSize", "logicalSessionTimeoutMinutes",
                             "readOnly", "internal", "operationTime", "$clusterTime")}
print(json.dumps(to_jsonable(sel), indent=1))
td = c.topology_description
print("topology", td.topology_type_name, [(redact(str(a)), s.server_type_name) for a, s in td.server_descriptions().items()])
p = c.admin.command("ping")
print("ping reply", to_jsonable(p))
c.close()
