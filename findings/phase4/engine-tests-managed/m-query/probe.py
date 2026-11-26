#!/usr/bin/env python
"""Connectivity probe for test m-query. Owns database mt_query only; prints no credentials."""
import json, os, warnings, time
warnings.filterwarnings("ignore", category=UserWarning)
from bson import json_util
from pymongo import MongoClient

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(HERE), "managed.env")

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

env = load_env(ENV)
t0 = time.time()
c = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, appname="m-query-probe")
hello = c.admin.command("hello")
bi = c.admin.command("buildInfo")
db = c["mt_query"]
print(json.dumps({
    "connect_and_hello_ms": round((time.time() - t0) * 1000),
    "hello": json.loads(json_util.dumps(hello)),
    "buildInfo_version": bi.get("version"),
    "buildInfo_keys": sorted(bi.keys()),
    "mt_query_collections": db.list_collection_names(),
}, indent=1, default=str))
t1 = time.time(); c.admin.command("ping"); print("ping_ms", round((time.time()-t1)*1000))
