#!/usr/bin/env python
"""Read-only probe: buildInfo, hello, driver topology, and whether t_concern exists.

Reads LOCAL_URI from ../../engine-tests/local.env (never printed). Writes probe.json.
Touches no database other than reading the database name list.
"""
import json
import os
import re

from pymongo import MongoClient

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "..", "engine-tests", "local.env")


def load_uri():
    with open(ENV) as f:
        for line in f:
            line = line.strip()
            if line.startswith("LOCAL_URI="):
                v = line.split("=", 1)[1].strip()
                if v and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                return v
    raise SystemExit("LOCAL_URI not found")


def jsonable(o):
    try:
        json.dumps(o)
        return o
    except (TypeError, ValueError):
        pass
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    return repr(o)


uri = load_uri()
c = MongoClient(uri, serverSelectionTimeoutMS=15000, socketTimeoutMS=60000)
bi = c.admin.command("buildInfo")
hello = c.admin.command("hello")
td = c.topology_description
names = c.list_database_names()
out = {
    "buildInfo": jsonable(bi),
    "hello": jsonable(hello),
    "driver_topology_type": td.topology_type_name,
    "driver_server_types": [s.server_type_name for s in td.server_descriptions().values()],
    "t_concern_exists_before_test": "t_concern" in names,
    "database_count": len(names),
}
with open(os.path.join(HERE, "probe.json"), "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps({k: out[k] for k in ("driver_topology_type", "driver_server_types", "t_concern_exists_before_test")}))
print("buildInfo.version:", bi.get("version"), "| gitVersion:", bi.get("gitVersion"))
print("hello:", json.dumps(jsonable(hello))[:1500])
c.close()
