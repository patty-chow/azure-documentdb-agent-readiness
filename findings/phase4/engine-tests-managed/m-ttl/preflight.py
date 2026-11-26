#!/usr/bin/env python
"""m-ttl preflight: connectivity, hello.localTime presence, RTT, and whether mt_ttl already exists.
Reads ../managed.env; never prints secrets or URIs."""
import os, re, sys, time, warnings, datetime as dt
warnings.filterwarnings("ignore", message=".*CosmosDB.*")
from pymongo import MongoClient
HERE = os.path.dirname(os.path.abspath(__file__))
env = {}
for line in open(os.path.join(HERE, "..", "managed.env")):
    line = line.rstrip("\n")
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
c = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=15000, socketTimeoutMS=30000, connectTimeoutMS=15000, appname="m-ttl-preflight")
t0 = dt.datetime.now(dt.timezone.utc); h = c.admin.command("hello"); t1 = dt.datetime.now(dt.timezone.utc)
lt = h.get("localTime")
print("hello keys:", sorted(h.keys()))
print("maxWireVersion:", h.get("maxWireVersion"), "msg:", h.get("msg"), "internal:", h.get("internal"))
print("localTime present:", lt is not None, "type:", type(lt).__name__)
rtt = (t1 - t0).total_seconds()
if lt is not None:
    if lt.tzinfo is None: lt = lt.replace(tzinfo=dt.timezone.utc)
    mid = t0 + (t1 - t0) / 2
    print("offset_s(server-client): %.3f  rtt_s: %.3f" % ((lt - mid).total_seconds(), rtt))
for i in range(3):
    a = time.perf_counter(); c.admin.command("ping"); print("ping rtt_ms: %.1f" % ((time.perf_counter() - a) * 1000))
print("mt_ttl exists:", "mt_ttl" in c.list_database_names())
