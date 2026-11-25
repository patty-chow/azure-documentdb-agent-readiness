#!/usr/bin/env python
"""Read-only preflight for the write-read-concerns reproduce stage: is t_concern_rerun absent?
Reads LOCAL_URI from ../../engine-tests/local.env (never printed). Sends only listDatabases. Writes preflight.json."""
import json, os, datetime
from pymongo import MongoClient
HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.normpath(os.path.join(HERE, "..", "..", "engine-tests", "local.env"))
uri = None
for line in open(ENV):
    line = line.strip()
    if line.startswith("LOCAL_URI="):
        uri = line.split("=", 1)[1].strip().strip("'\"")
c = MongoClient(uri, serverSelectionTimeoutMS=15000)
names = c.list_database_names()
out = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "command": "client.list_database_names()  (listDatabases with nameOnly)",
       "t_concern_rerun_exists_before_run": "t_concern_rerun" in names,
       "t_concern_exists_before_run": "t_concern" in names,
       "database_count": len(names)}
json.dump(out, open(os.path.join(HERE, "preflight.json"), "w"), indent=2)
print(json.dumps(out))
c.close()
