#!/usr/bin/env python
"""Read-only probe: buildInfo, hello and whether database t_query exists. Never prints credentials."""
import json, os, re
from bson import json_util
from pymongo import MongoClient

ENV_PATH = os.environ.get("LOCAL_ENV", "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env")

def load_uri(path):
    for line in open(path):
        line = line.strip()
        if line.startswith("LOCAL_URI="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("LOCAL_URI not found")

uri = load_uri(ENV_PATH)
c = MongoClient(uri, serverSelectionTimeoutMS=10000)
bi = c.admin.command("buildInfo")
he = c.admin.command("hello")
print("buildInfo:", json_util.dumps(bi))
he.pop("localTime", None)
print("hello:", json_util.dumps(he))
print("t_query exists:", "t_query" in c.list_database_names())
