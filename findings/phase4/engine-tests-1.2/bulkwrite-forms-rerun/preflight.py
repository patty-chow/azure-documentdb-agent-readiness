#!/usr/bin/env python
"""Pre-flight for the bulkwrite-forms reproduction: record whether t_bulk_rerun exists before the run.
Runs one listDatabases filtered to that single name (touches no other database). Never prints secrets."""
import json
import os

from pymongo import MongoClient

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env"
uri = None
with open(ENV) as f:
    for line in f:
        line = line.strip()
        if line.startswith("LOCAL_URI="):
            uri = line.split("=", 1)[1].strip().strip("\"'")
c = MongoClient(uri, serverSelectionTimeoutMS=15000)
r = c.admin.command({"listDatabases": 1, "nameOnly": True, "filter": {"name": "t_bulk_rerun"}})
out = {"t_bulk_rerun_present_before_run": any(d.get("name") == "t_bulk_rerun" for d in r.get("databases", [])),
       "databases_returned": [d.get("name") for d in r.get("databases", [])]}
with open(os.path.join(HERE, "preflight.json"), "w") as f:
    json.dump({"command": "client.admin.command({'listDatabases':1,'nameOnly':True,'filter':{'name':'t_bulk_rerun'}})", "response": out}, f, indent=2)
print(json.dumps(out))
c.close()
