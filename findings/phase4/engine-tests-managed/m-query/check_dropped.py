#!/usr/bin/env python
"""Final check for test m-query: is database mt_query absent? Prints only that boolean and its collections."""
import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from pymongo import MongoClient
import run as r1
env = r1.load_env(r1.ENV_PATH)
c = MongoClient(env["MANAGED_URI"], serverSelectionTimeoutMS=30000, appname="m-query-check")
print(json.dumps({"mt_query_listed": "mt_query" in c.list_database_names(),
                  "mt_query_collections": c["mt_query"].list_collection_names()}))
c.close()
